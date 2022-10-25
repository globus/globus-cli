import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import (
    FORMAT_TEXT_TABLE,
    Field,
    field_formatters,
    formatted_print,
)


@command("list", short_help="List all User Credentials on an Endpoint")
@click.argument(
    "endpoint_id",
    metavar="ENDPOINT_ID",
)
@click.option(
    "--storage-gateway",
    default=None,
    type=click.UUID,
    help=(
        "Filter results to User Credentials on a Storage Gateway specified by "
        "this UUID"
    ),
)
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def user_credential_list(
    *,
    login_manager: LoginManager,
    endpoint_id: uuid.UUID,
    storage_gateway: uuid.UUID,
):
    """
    List the User Credentials on a given Globus Connect Server v5 Endpoint
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    res = gcs_client.get_user_credential_list(storage_gateway=storage_gateway)
    fields = [
        Field("ID", "id"),
        Field("Display Name", "display_name"),
        Field(
            "Globus Identity",
            "identity_id",
            formatter=field_formatters.IdentityFormatter(
                login_manager.get_auth_client()
            ),
        ),
        Field("Local Username", "username"),
        Field("Invalid", "invalid"),
    ]
    formatted_print(res, text_format=FORMAT_TEXT_TABLE, fields=fields)
