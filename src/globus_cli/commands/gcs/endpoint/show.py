import uuid

from globus_cli.commands.gcs.endpoint._common import GCS_ENDPOINT_FIELDS
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


@command("show")
@endpoint_id_arg
@LoginManager.requires_login("transfer")
def show_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
) -> None:
    """Describe a GCS Endpoint"""
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    res = gcs_client.get_endpoint()

    display(res, text_mode=TextMode.text_record, fields=GCS_ENDPOINT_FIELDS)
