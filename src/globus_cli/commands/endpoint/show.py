import click

from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import FORMAT_TEXT_RECORD, FormatField, formatted_print

STANDARD_FIELDS = (
    ("Display Name", "display_name"),
    ("ID", "id"),
    ("Owner", "owner_string"),
    FormatField("Description", "description", wrap_enabled=True),
    ("Activated", "activated"),
    ("Shareable", "shareable"),
    ("Department", "department"),
    ("Keywords", "keywords"),
    ("Endpoint Info Link", "info_link"),
    ("Contact E-mail", "contact_email"),
    ("Organization", "organization"),
    ("Department", "department"),
    ("Other Contact Info", "contact_info"),
    ("Visibility", "public"),
    ("Default Directory", "default_directory"),
    ("Force Encryption", "force_encryption"),
    ("Managed Endpoint", lambda res: bool(res["subscription_id"])),
    ("Subscription ID", "subscription_id"),
    ("Legacy Name", "canonical_name"),
    ("Local User Info Available", "local_user_info_available"),
)

GCP_FIELDS = STANDARD_FIELDS + (
    ("GCP Connected", "gcp_connected"),
    ("GCP Paused (macOS only)", "gcp_paused"),
)


@command("show")
@endpoint_id_arg
@click.option("--skip-endpoint-type-check", is_flag=True, hidden=True)
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def endpoint_show(
    *, login_manager: LoginManager, endpoint_id: str, skip_endpoint_type_check: bool
) -> None:
    """Display a detailed endpoint definition"""
    transfer_client = login_manager.get_transfer_client()
    if not skip_endpoint_type_check:
        Endpointish(
            endpoint_id, transfer_client=transfer_client
        ).assert_is_not_gcsv5_collection()

    res = transfer_client.get_endpoint(endpoint_id)

    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=GCP_FIELDS if res["is_globus_connect"] else STANDARD_FIELDS,
    )
