import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import (
    FORMAT_TEXT_RECORD,
    Field,
    field_formatters,
    formatted_print,
)

from .._common import task_id_arg

TASK_FIELDS = [
    Field(
        "State",
        "[state, state_description]",
        formatter=field_formatters.ParentheticalDescriptionFormatter(),
    ),
    Field("Index ID", "index_id"),
    Field("Message", "message"),
    Field("Creation Date", "creation_date"),
    Field("Completion Date", "completion_date"),
]


@command("show")
@task_id_arg
@LoginManager.requires_login(LoginManager.SEARCH_RS)
def show_command(*, login_manager: LoginManager, task_id: uuid.UUID):
    """Display a Task"""
    search_client = login_manager.get_search_client()
    formatted_print(
        search_client.get_task(task_id),
        fields=TASK_FIELDS,
        text_format=FORMAT_TEXT_RECORD,
    )
