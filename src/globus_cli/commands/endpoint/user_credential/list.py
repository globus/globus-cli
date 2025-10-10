from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, display, formatters


@command("list", short_help="List all User Credentials on an Endpoint.")
@endpoint_id_arg
@click.option(
    "--storage-gateway",
    default=globus_sdk.MISSING,
    type=click.UUID,
    help=(
        "Filter results to User Credentials on a Storage Gateway specified by "
        "this UUID"
    ),
)
@LoginManager.requires_login("auth", "transfer")
def user_credential_list(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    storage_gateway: uuid.UUID | globus_sdk.MissingType,
) -> None:
    """
    List all of your User Credentials on a Globus Connect Server v5 Endpoint.
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()
    res = gcs_client.get_user_credential_list(storage_gateway=storage_gateway)
    fields = [
        Field("ID", "id"),
        Field("Display Name", "display_name"),
        Field(
            "Globus Identity",
            "identity_id",
            formatter=formatters.auth.IdentityIDFormatter(auth_client),
        ),
        Field("Local Username", "username"),
        Field("Invalid", "invalid"),
    ]
    display(res, text_mode=display.TABLE, fields=fields)
