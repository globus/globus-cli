import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from .._common import INDEX_FIELDS, index_id_arg


@command("show")
@index_id_arg
@LoginManager.requires_login("search")
def show_command(*, login_manager: LoginManager, index_id: uuid.UUID) -> None:
    """Display information about an index"""
    search_client = login_manager.get_search_client()
    display(
        search_client.get_index(index_id),
        text_mode=TextMode.text_record,
        fields=INDEX_FIELDS,
    )
