import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, TextMode, display, formatters

STANDARD_FIELDS = [
    Field("ID", "id"),
    Field("Display Name", "display_name"),
    Field("High Assurance", "high_assurance"),
    Field("Allowed Domains", "allowed_domains", formatter=formatters.SortedArray),
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
    display(res, text_mode=TextMode.text_table, fields=STANDARD_FIELDS)
