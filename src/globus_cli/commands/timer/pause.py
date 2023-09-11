import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display


@command("pause", short_help="Pause a timer")
@click.argument("JOB_ID", type=click.UUID)
@LoginManager.requires_login("timer")
def pause_command(login_manager: LoginManager, *, job_id: uuid.UUID) -> None:
    """
    Pause a timer.
    """
    timer_client = login_manager.get_timer_client()
    paused = timer_client.pause_job(job_id)
    display(
        paused,
        text_mode=TextMode.text_raw,
        simple_text=paused["message"],
    )
