from __future__ import annotations

import uuid

from globus_cli.commands.flows._fields import web_input_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, web_input_id_arg
from globus_cli.termio import display


@command("show")
@web_input_id_arg
@LoginManager.requires_login("auth", "flows")
def show_command(login_manager: LoginManager, *, web_input_id: uuid.UUID) -> None:
    """
    Show a web input.
    """
    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    response = flows_client.get_web_input(web_input_id)
    fields = web_input_format_fields(auth_client, response.data)

    display(response, fields=fields, text_mode=display.RECORD)
