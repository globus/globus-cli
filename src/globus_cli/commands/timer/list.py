from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from ._common import JOB_FORMAT_FIELDS


@command("list", short_help="List your jobs")
@LoginManager.requires_login("timer")
def list_command(*, login_manager: LoginManager) -> None:
    """
    List your Timer jobs.
    """
    timer_client = login_manager.get_timer_client()
    response = timer_client.list_jobs(query_params={"order": "submitted_at asc"})
    display(
        response["jobs"],
        text_mode=TextMode.text_record_list,
        fields=JOB_FORMAT_FIELDS,
    )
