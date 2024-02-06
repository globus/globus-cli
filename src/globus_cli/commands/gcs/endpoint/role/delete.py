import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import TextMode, display


@command(
    "show",
)
@endpoint_id_arg
@click.argument("ROLE_ID", type=click.UUID)
@LoginManager.requires_login("transfer")
def delete_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    role_id: uuid.UUID,
) -> None:
    """Delete a role from a GCS Endpoint."""
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    res = gcs_client.delete_role(role_id)

    display(res, text_mode=TextMode.text_raw, response_key="message")
