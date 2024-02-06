from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, TextMode, display
from globus_cli.utils import resolve_principal_urn

from ..._common import index_id_arg, resolved_principals_field


@command("create")
@index_id_arg
@click.argument("ROLE_NAME")
@click.argument("PRINCIPAL")
@click.option(
    "--type",
    "principal_type",
    type=click.Choice(("identity", "group")),
    help=(
        "The type of the principal. "
        "If the principal is given as a URN, it will be checked against any provided "
        "'type'. If a non-URN string is given, the type will be used to format the "
        "principal as a URN."
    ),
)
@LoginManager.requires_login("auth", "search")
def create_command(
    login_manager: LoginManager,
    *,
    index_id: uuid.UUID,
    role_name: str,
    principal: str,
    principal_type: t.Literal["identity", "group"] | None,
) -> None:
    """
    Create a role (requires admin or owner)

    PRINCIPAL is expected to be an identity or group ID, a principal URN, or a username.

    Example usage:
       globus-search index role create "$index_id" admin "globus@globus.org"
       globus-search index role create "$index_id" writer "$group_id" --type group
    """
    search_client = login_manager.get_search_client()
    auth_client = login_manager.get_auth_client()

    principal_urn = resolve_principal_urn(
        auth_client=auth_client,
        principal_type=principal_type,
        principal=principal,
        principal_type_key="--type",
    )

    role_doc = {"role_name": role_name, "principal": principal_urn}
    display(
        search_client.create_role(index_id, data=role_doc),
        text_mode=TextMode.text_record,
        fields=[
            Field("Index ID", "index_id"),
            Field("Role ID", "id"),
            Field("Role Name", "role_name"),
            resolved_principals_field(auth_client),
        ],
    )
