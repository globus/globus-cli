import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from ._common import DELETED_JOB_FORMAT_FIELDS


@command("delete", short_help="Delete a timer job", hidden=True)
@click.argument("JOB_ID", type=click.UUID)
@LoginManager.requires_login("timer")
def delete_command(*, login_manager: LoginManager, job_id: uuid.UUID) -> None:
    """
    Delete a Timer job.

    The contents of the deleted job is printed afterwards.
    """
    timer_client = login_manager.get_timer_client()
    deleted = timer_client.delete_job(job_id)
    display(
        deleted,
        text_mode=TextMode.text_record,
        fields=DELETED_JOB_FORMAT_FIELDS,
    )
