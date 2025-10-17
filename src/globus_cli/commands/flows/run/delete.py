from __future__ import annotations

import uuid

from globus_cli.commands.flows._fields import flow_run_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import display


@command("delete")
@run_id_arg
@LoginManager.requires_login("flows")
def delete_command(login_manager: LoginManager, *, run_id: uuid.UUID) -> None:
    """
    Delete a run.
    """

    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    res = flows_client.delete_run(run_id)

    fields = flow_run_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)
