from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.commands.flows._fields import web_input_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, web_input_id_arg
from globus_cli.termio import Field, display


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

    def _formatted_context_and_options(res: globus_sdk.GlobusHTTPResponse) -> None:
        fields = web_input_format_fields(auth_client, res.data)
        display(res, fields=fields, text_mode=display.RECORD)

        context = res.get("context") or {}
        if context.get("presentation_style") == "table":
            display(
                context.get("rows") or [],
                fields=[Field("Field", "field"), Field("Value", "value")],
                text_mode=display.TABLE,
                text_preamble="\nContext:\n",
            )
        else:
            click.echo(f"\nContext:\n    {context.get('text', '')}")

        options = res.get("options")
        if options:
            display(
                options,
                fields=[Field("Option ID", "option_id"), Field("Label", "label")],
                text_mode=display.TABLE,
                text_preamble="\nOptions:\n",
            )

    display(response, text_mode=_formatted_context_and_options)
