import click

from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, TextMode, display, formatters

STANDARD_FIELDS = [
    Field("Display Name", "display_name"),
    Field("ID", "id"),
    Field("Owner", "owner_string"),
    Field("Description", "description", wrap_enabled=True),
    Field("Activated", "activated"),
    Field("Shareable", "shareable"),
    Field("Department", "department"),
    Field("Keywords", "keywords"),
    Field("Endpoint Info Link", "info_link"),
    Field("Contact E-mail", "contact_email"),
    Field("Organization", "organization"),
    Field("Department", "department"),
    Field("Other Contact Info", "contact_info"),
    Field("Visibility", "public"),
    Field("Default Directory", "default_directory"),
    Field("Force Encryption", "force_encryption"),
    Field("Managed Endpoint", "subscription_id", formatter=formatters.FuzzyBool),
    Field("Subscription ID", "subscription_id"),
    Field("Legacy Name", "canonical_name"),
    Field("Local User Info Available", "local_user_info_available"),
]

GCP_FIELDS = STANDARD_FIELDS + [
    Field("GCP Connected", "gcp_connected"),
    Field("GCP Paused (macOS only)", "gcp_paused"),
]


@command("show")
@endpoint_id_arg
@click.option("--skip-endpoint-type-check", is_flag=True, hidden=True)
@LoginManager.requires_login("transfer")
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

    display(
        res,
        text_mode=TextMode.text_record,
        fields=GCP_FIELDS if res["is_globus_connect"] else STANDARD_FIELDS,
    )
