import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_TABLE, Field, formatted_print

from .._common import index_id_arg

TASK_FIELDS = [
    Field("State", "state"),
    Field("Task ID", "task_id"),
    Field("Creation Date", "creation_date"),
    Field("Completion Date", "completion_date"),
]


@command("list", short_help="List recent Tasks for an index")
@index_id_arg
@LoginManager.requires_login(LoginManager.SEARCH_RS)
def list_command(*, login_manager: LoginManager, index_id: uuid.UUID):
    """List the 1000 most recent Tasks for an index"""
    search_client = login_manager.get_search_client()
    formatted_print(
        search_client.get_task_list(index_id),
        fields=TASK_FIELDS,
        text_format=FORMAT_TEXT_TABLE,
        response_key="tasks",
    )
