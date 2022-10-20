import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_TABLE, formatted_print


def _parse_allowed_domains(res):
    return ", ".join(sorted(res["allowed_domains"]))


STANDARD_FIELDS = [
    ("ID", "id"),
    ("Display Name", "display_name"),
    ("High Assurance", "high_assurance"),
    ("Allowed Domains", _parse_allowed_domains),
]


@command("list", short_help="List all User Credentials on an Endpoint")
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
    List the User Credentials on a given Globus Connect Server v5 Endpoint
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    res = gcs_client.get_storage_gateway_list()
    formatted_print(res, text_format=FORMAT_TEXT_TABLE, fields=STANDARD_FIELDS)
