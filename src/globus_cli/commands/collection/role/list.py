import uuid

import click

from globus_cli.commands.collection.role._fields import collection_role_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import display


@command("list")
@collection_id_arg
@click.option("--all-roles", is_flag=True, help="Include all collection roles.")
@LoginManager.requires_login("transfer")
def list_command(
    login_manager: LoginManager,
    *,
    collection_id: uuid.UUID,
    all_roles: bool,
) -> None:
    """List roles on a particular Collection."""
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)
    auth_client = login_manager.get_auth_client()

    if all_roles:
        res = gcs_client.get_role_list(collection_id, include="all_roles")
    else:
        res = gcs_client.get_role_list(collection_id)

    fields = collection_role_format_fields(auth_client, res.data)
    display(
        res,
        text_mode=display.RECORD_LIST,
        fields=fields,
    )
