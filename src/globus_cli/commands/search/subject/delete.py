import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, TextMode, display, formatters

from .._common import index_id_arg


@command("delete")
@index_id_arg
@click.argument("subject")
@LoginManager.requires_login("search")
def delete_command(
    *,
    index_id: uuid.UUID,
    subject: str,
    login_manager: LoginManager,
) -> None:
    """Delete a subject (requires writer, admin, or owner)

    Delete a submit a delete_by_subject task on an index. This requires writer or
    stronger privileges on the index.

    Returns the 'task_id' for the deletion task. Deletions are not guaranteed to be
    immediate, but will be put into the task queue for that index. Monitor tasks using
    commands like 'globus search task show'
    """
    search_client = login_manager.get_search_client()
    display(
        search_client.delete_subject(index_id, subject),
        text_mode=TextMode.text_record,
        fields=[
            Field(
                "Message",
                "@",
                formatter=formatters.StaticStringFormatter(
                    "delete-by-subject task successfully submitted"
                ),
            ),
            Field("Task ID", "task_id"),
        ],
    )
