from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, web_input_id_arg
from globus_cli.termio import Field, display


@command("respond")
@web_input_id_arg
@click.argument("option_id", metavar="OPTION_ID", type=click.UUID, required=True)
@LoginManager.requires_login("flows")
def respond_command(
    login_manager: LoginManager,
    *,
    web_input_id: uuid.UUID,
    option_id: uuid.UUID,
) -> None:
    """
    Respond to a web input.

    For "selection" type web inputs, OPTION_ID is the ID of one of the web input's
    available options.
    """

    flows_client = login_manager.get_flows_client()
    response = flows_client.respond_to_web_input(web_input_id, value=option_id)

    display(
        response,
        text_mode=display.RECORD,
        fields=[Field("Status", "status")],
    )
