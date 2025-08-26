import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import display


@command("delete")
@collection_id_arg
@click.argument("ROLE_ID", type=click.UUID)
@LoginManager.requires_login("transfer")
def delete_command(
    login_manager: LoginManager,
    *,
    collection_id: uuid.UUID,
    role_id: uuid.UUID,
) -> None:
    """Delete a particular role on a Collection."""
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)
    res = gcs_client.delete_role(role_id)
    display(res, text_mode=display.RAW, response_key="code")
