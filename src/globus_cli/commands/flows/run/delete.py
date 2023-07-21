from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import Field, TextMode, display, formatters


@command("delete", short_help="Delete a run")
@run_id_arg
@LoginManager.requires_login("flows")
def delete_command(login_manager: LoginManager, *, run_id: uuid.UUID) -> None:
    """
    Delete a run
    """

    flows_client = login_manager.get_flows_client()

    fields = [
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        Field("Run ID", "run_id"),
        Field("Run Label", "label"),
        Field("Started At", "start_time", formatter=formatters.Date),
        Field("Completed At", "completion_time", formatter=formatters.Date),
        Field("Status", "status"),
    ]

    res = flows_client.delete_run(run_id)
    display(res, fields=fields, text_mode=TextMode.text_record)
