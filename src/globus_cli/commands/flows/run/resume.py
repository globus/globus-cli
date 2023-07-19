from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import Field, TextMode, display, formatters


@command("resume")
@run_id_arg
@LoginManager.requires_login("flows")
def resume_command(login_manager: LoginManager, run_id: uuid.UUID) -> None:
    """
    Resume a run
    """
    flows_client = login_manager.get_flows_client()
    run_doc = flows_client.get_run(run_id)
    flow_id = run_doc["flow_id"]

    specific_flow_client = login_manager.get_specific_flow_client(flow_id)

    fields = [
        Field("Run ID", "run_id"),
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        Field("Status", "status"),
        Field("Run Label", "label"),
        Field("Run Tags", "tags", formatter=formatters.Array),
        Field("Started At", "start_time", formatter=formatters.Date),
    ]

    res = specific_flow_client.resume_run(run_id)
    display(res, fields=fields, text_mode=TextMode.text_record)
