import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from .._common import index_id_arg


@command("delete")
@LoginManager.requires_login("search")
@index_id_arg
def delete_command(login_manager: LoginManager, *, index_id: uuid.UUID) -> None:
    """Delete a Search index."""
    search_client = login_manager.get_search_client()
    display(
        search_client.delete_index(index_id),
        simple_text=(
            f"Index {index_id} is now marked for deletion.\n"
            "It will be fully deleted after cleanup steps complete."
        ),
    )
