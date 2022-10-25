import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import (
    FORMAT_TEXT_TABLE,
    Field,
    field_formatters,
    formatted_print,
)

STANDARD_FIELDS = [
    Field("ID", "id"),
    Field("Display Name", "display_name"),
    Field("High Assurance", "high_assurance"),
    Field("Allowed Domains", "allowed_domains", formatter=field_formatters.SortedArray),
]


@command("list", short_help="List the Storage Gateways on an Endpoint")
@click.argument(
    "endpoint_id",
    metavar="ENDPOINT_ID",
)
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def storage_gateway_list(
    *,
    login_manager: LoginManager,
    endpoint_id,
):
    """
    List the Storage Gateways on a given Globus Connect Server v5 Endpoint
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    res = gcs_client.get_storage_gateway_list()
    formatted_print(res, text_format=FORMAT_TEXT_TABLE, fields=STANDARD_FIELDS)
