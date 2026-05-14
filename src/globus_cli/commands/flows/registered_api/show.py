from __future__ import annotations

import uuid

import click

from globus_cli.commands.flows._fields import registered_api_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display


@command("show")
@click.argument("registered_api_id", type=click.UUID)
@LoginManager.requires_login("auth", "flows")
def show_command(login_manager: LoginManager, *, registered_api_id: uuid.UUID) -> None:
    """
    Show a registered API.
    """
    flows_client = login_manager.get_flows_client()

    res = flows_client.get_registered_api(registered_api_id)

    auth_client = login_manager.get_auth_client()
    fields = registered_api_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)
