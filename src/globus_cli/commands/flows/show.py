from __future__ import annotations

import uuid

from globus_cli.commands.flows._fields import flow_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, flow_id_arg
from globus_cli.termio import display


@command("show")
@flow_id_arg
@LoginManager.requires_login("flows")
def show_command(login_manager: LoginManager, *, flow_id: uuid.UUID) -> None:
    """
    Show a flow.
    """
    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    res = flows_client.get_flow(flow_id)

    fields = flow_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)
