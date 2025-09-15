from __future__ import annotations

import functools
import typing as t

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display
from globus_cli.utils import LazyDict, is_uuid

from ._common import DECORATED_SCOPE_FIELDS, BatchScopeStringResolver


@command("show")
@click.argument("SCOPE_ID_OR_STRING", type=str)
@LoginManager.requires_login("auth")
def show_command(login_manager: LoginManager, *, scope_id_or_string: str) -> None:
    """Show a scope by ID or string."""
    auth_client = login_manager.get_auth_client()

    if is_uuid(scope_id_or_string):
        show_scope_by_id(auth_client, scope_id_or_string)
    else:
        show_scope_by_string(auth_client, scope_id_or_string)


def show_scope_by_id(auth_client: globus_sdk.AuthClient, scope_id: str) -> None:
    scope_resp = auth_client.get_scope(scope_id)

    decorate_scope_response(auth_client, scope_resp["scope"])

    display(
        scope_resp,
        text_mode=display.RECORD,
        fields=DECORATED_SCOPE_FIELDS,
        response_key="scope",
    )


def show_scope_by_string(auth_client: globus_sdk.AuthClient, scope_string: str) -> None:
    scope_resp = auth_client.get_scopes(scope_strings=[scope_string])

    decorate_scope_response(auth_client, scope_resp["scopes"][0])

    display(
        scope_resp,
        text_mode=display.RECORD,
        fields=DECORATED_SCOPE_FIELDS,
        response_key=lambda resp: resp["scopes"][0],
    )


def decorate_scope_response(
    auth_client: globus_sdk.AuthClient,
    scope: dict[str, t.Any],
) -> None:
    """
    Decorates the dependent scopes of a get-scope response.

    Every dependent scope dict has a "scope_string" lazy-loader added to it that will
    resolve the scope string by querying globus auth (with batching and caching).
    """
    dependent_scopes = scope.get("dependent_scopes")
    if not dependent_scopes:
        return

    # Create a batch resolver so that we resolve all dependent scope strings at once.
    dependent_scope_ids = [dependent["scope"] for dependent in dependent_scopes]
    resolver = BatchScopeStringResolver(auth_client, dependent_scope_ids)

    # Replace the dependent scopes with LazyDicts.
    scope["dependent_scopes"] = [LazyDict(dependent) for dependent in dependent_scopes]
    for dependent in scope["dependent_scopes"]:
        load_scope_string = functools.partial(resolver.resolve, dependent["scope"])
        dependent.register_loader("scope_string", load_scope_string)
