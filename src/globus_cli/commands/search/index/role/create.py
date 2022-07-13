from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print

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
@LoginManager.requires_login(LoginManager.SEARCH_RS, LoginManager.AUTH_RS)
def create_command(
    *,
    index_id: uuid.UUID,
    role_name: str,
    principal: str,
    principal_type: str | None,
    login_manager: LoginManager,
):
    """
    Create a role (requires admin or owner)

    PRINCIPAL is expected to be an identity or group ID, a principal URN, or a username.

    Example usage:
       globus-search index role create "$index_id" admin "globus@globus.org"
       globus-search index role create "$index_id" writer "$group_id" --type group
    """
    search_client = login_manager.get_search_client()
    auth_client = login_manager.get_auth_client()

    if principal.startswith("urn:"):
        if principal_type == "identity" and not principal.startswith(
            "urn:globus:auth:identity:"
        ):
            raise click.UsageError(
                f"--type=identity but '{principal}' is not a valid identity URN"
            )
        if principal_type == "group" and not principal.startswith(
            "urn:globus:groups:id:"
        ):
            raise click.UsageError(
                f"--type=group but '{principal}' is not a valid group URN"
            )
    else:
        if principal_type == "identity" or principal_type is None:
            resolved = auth_client.maybe_lookup_identity_id(principal)
            if resolved is None:
                raise click.UsageError(
                    f"{principal} does not appear to be a valid principal"
                )
            principal = f"urn:globus:auth:identity:{resolved}"
        elif principal_type == "group":
            principal = f"urn:globus:groups:id:{principal}"
        else:
            raise NotImplementedError("unrecognized principal_type")

    role_doc = {"role_name": role_name, "principal": principal}
    formatted_print(
        search_client.create_role(index_id, data=role_doc),
        text_format=FORMAT_TEXT_RECORD,
        fields=[
            ("Index ID", "index_id"),
            ("Role ID", "id"),
            ("Role Name", "role_name"),
            resolved_principals_field(auth_client),
        ],
    )
