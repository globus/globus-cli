from __future__ import annotations

import uuid

import click

from globus_cli.commands.flows._fields import registered_api_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display


@command("show")
@click.argument("registered_api_id")
@LoginManager.requires_login("auth", "flows")
def show_command(login_manager: LoginManager, *, registered_api_id: str) -> None:
    """
    Show a registered API.

    Accepts a registered API UUID.
    """
    flows_client = login_manager.get_flows_client()

    # Convert string to UUID if it's a valid UUID
    try:
        api_id: uuid.UUID | str = uuid.UUID(registered_api_id)
    except ValueError:
        api_id = registered_api_id

    res = flows_client.get_registered_api(api_id)

    auth_client = login_manager.get_auth_client()
    fields = registered_api_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)
