from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display, formatters

from .._common import INDEX_FIELDS

INDEX_LIST_FIELDS = INDEX_FIELDS + [
    Field("Permissions", "permissions", formatter=formatters.Array),
]


@command("list")
@LoginManager.requires_login("search")
def list_command(login_manager: LoginManager) -> None:
    """List indices where you have some permissions."""
    search_client = login_manager.get_search_client()
    display(
        search_client.index_list(), fields=INDEX_LIST_FIELDS, text_mode=display.TABLE
    )
