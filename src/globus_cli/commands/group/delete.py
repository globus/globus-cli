import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import group_id_arg


@group_id_arg
@command("delete")
@LoginManager.requires_login("groups")
def group_delete(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
) -> None:
    """Delete a group"""
    groups_client = login_manager.get_groups_client()

    response = groups_client.delete_group(group_id)

    display(response, simple_text="Group deleted successfully")
