import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from ._common import JOB_FORMAT_FIELDS


@command("show", short_help="Display a Timer job")
@click.argument("JOB_ID", type=click.UUID)
@LoginManager.requires_login("timer")
def show_command(*, login_manager: LoginManager, job_id: uuid.UUID) -> None:
    """
    Display information about a particular job.
    """
    timer_client = login_manager.get_timer_client()
    response = timer_client.get_job(job_id)
    display(response, text_mode=TextMode.text_record, fields=JOB_FORMAT_FIELDS)
