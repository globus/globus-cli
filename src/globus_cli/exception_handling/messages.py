"""
Reusable message strings and message printing helpers for exception hooks.
"""

from __future__ import annotations

import json
import os

import click
import globus_sdk.gare

from globus_cli.login_manager import is_client_login
from globus_cli.types import JsonValue

DEFAULT_SESSION_REAUTH_MESSAGE = (
    "The resource you are trying to access requires you to re-authenticate."
)
DEFAULT_CONSENT_REAUTH_MESSAGE = (
    "The resource you are trying to access requires you to "
    "consent to additional access for the Globus CLI."
)

_UNAUTHORIZED_CLIENT_MESSAGE: str = (
    "Invalid Authentication provided.\n\n"
    "'GLOBUS_CLI_CLIENT_ID' and 'GLOBUS_CLI_CLIENT_SECRET' are set but do "
    "not appear to be valid client credentials.\n"
    "Please check that the values are correctly set with no missing "
    "characters.\n"
)
_UNAUTHORIZED_USER_MESSAGE: str = (
    "No Authentication provided.\n"
    "Please run:\n\n"
    "    globus login\n\n"
    "to ensure that you are logged in."
)


def emit_unauthorized_message() -> None:
    """
    Emit messaging for unauthorized usage, in which there are no tokens or the
    provided credentials appear invalid.
    """
    if is_client_login():
        click.echo(
            click.style("MissingLoginError: ", fg="yellow")
            + _UNAUTHORIZED_CLIENT_MESSAGE,
            err=True,
        )
        if not _client_id_is_valid():
            msg = "'GLOBUS_CLI_CLIENT_ID' does not appear to be a valid client ID."
            click.secho(msg, bold=True, fg="red", err=True)
        if not _client_secret_appears_valid():
            msg = (
                "'GLOBUS_CLI_CLIENT_SECRET' does not appear to "
                "be a valid client secret."
            )
            click.secho(msg, bold=True, fg="red", err=True)

    else:
        click.echo(
            click.style("MissingLoginError: ", fg="yellow")
            + _UNAUTHORIZED_USER_MESSAGE,
            err=True,
        )


def _client_id_is_valid() -> bool:
    """
    Check if the CLI client ID appears to be in an invalid format.
    Assumes that the client secret env var is set.
    """
    import uuid

    try:
        uuid.UUID(os.environ["GLOBUS_CLI_CLIENT_ID"])
        return True
    except ValueError:
        return False


def _client_secret_appears_valid() -> bool:
    """
    Check if the CLI client secret appears to be in an invalid format.
    Assumes that the client secret env var is set.

    This check is known to be sensitive to potential changes in Globus Auth.
    After discussion with the Auth team, we can use this check as long as we treat it
    as a fallible heuristic. Messaging should reflect "appears to be invalid", etc.
    """
    import base64

    secret = os.environ["GLOBUS_CLI_CLIENT_SECRET"]
    if len(secret) < 30:
        return False

    try:
        base64.b64decode(secret.encode("utf-8"))
    except ValueError:
        return False

    return True


def emit_session_update_message(
    *,
    policies: list[str] | None,
    identities: list[str] | None,
    domains: list[str] | None,
    scopes: list[str] | None = None,
    message: str = DEFAULT_SESSION_REAUTH_MESSAGE,
) -> None:
    click.echo(message)
    scope_args = "".join(f" --scope '{s}'" for s in scopes or ())

    if identities or domains:
        # check both values in this assignment to convince mypy of correctness
        target_list: list[str] = (
            identities if identities else domains if domains else []
        )
        update_target = " ".join(target_list)
        click.echo(
            "\nPlease run:\n\n"
            f"    globus session update {update_target}{scope_args}\n\n"
            "to re-authenticate with the required identities."
        )
    elif policies:
        click.echo(
            "\nPlease run:\n\n"
            f"    globus session update --policy '{','.join(policies)}'{scope_args}\n\n"
            "to re-authenticate with the required identities."
        )
    else:
        click.echo(
            f'\nPlease use "globus session update {scope_args}" to re-authenticate '
            "with specific identities."
        )


def emit_consent_required_message(
    *,
    required_scopes: list[str],
    message: str = DEFAULT_CONSENT_REAUTH_MESSAGE,
) -> None:
    click.echo(message)

    click.echo(
        "\nPlease run:\n\n"
        "  globus session consent {}\n\n".format(
            " ".join(f"'{x}'" for x in required_scopes)
        )
        + "to login with the required scopes."
    )


def emit_message_for_gare(
    gare: globus_sdk.gare.GARE, message: str | None = None
) -> None:
    required_scopes = gare.authorization_parameters.required_scopes
    session_policies = gare.authorization_parameters.session_required_policies
    session_identities = gare.authorization_parameters.session_required_identities
    session_domains = gare.authorization_parameters.session_required_single_domain

    requires_update = bool(session_policies or session_identities or session_domains)

    if requires_update:
        emit_session_update_message(
            policies=session_policies,
            identities=session_identities,
            domains=session_domains,
            scopes=required_scopes,
            message=message or DEFAULT_SESSION_REAUTH_MESSAGE,
        )
    elif required_scopes:
        emit_consent_required_message(
            required_scopes=required_scopes,
            message=message or DEFAULT_CONSENT_REAUTH_MESSAGE,
        )


def pretty_json(data: JsonValue, compact: bool = False) -> str:
    if compact:
        return json.dumps(data, separators=(",", ":"), sort_keys=True)
    return json.dumps(data, indent=2, sort_keys=True)
