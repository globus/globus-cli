import uuid

import click

from globus_cli.commands.gcs.endpoint.role._common import role_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


@command(
    "show",
)
@endpoint_id_arg
@click.argument("ROLE_ID", type=click.UUID)
@LoginManager.requires_login("transfer")
def show_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    role_id: uuid.UUID,
) -> None:
    """Describe a particular role on a GCS Endopint."""
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()

    res = gcs_client.get_role(role_id)

    display(res, text_mode=TextMode.text_record, fields=role_fields(auth_client))
