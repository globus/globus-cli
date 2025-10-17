from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.commands.flows._fields import flow_run_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import display


def _none_to_missing(
    ctx: click.Context, param: click.Parameter, value: bool | None
) -> bool | globus_sdk.MissingType:
    if value is None:
        return globus_sdk.MISSING
    return value


@command("show")
@run_id_arg
@click.option(
    "--include-flow-description", is_flag=True, default=None, callback=_none_to_missing
)
@LoginManager.requires_login("flows")
def show_command(
    login_manager: LoginManager,
    *,
    run_id: uuid.UUID,
    include_flow_description: bool | globus_sdk.MissingType,
) -> None:
    """
    Show a run.
    """

    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    response = flows_client.get_run(
        run_id, include_flow_description=include_flow_description
    )

    fields = flow_run_format_fields(auth_client, response.data)

    display(response, fields=fields, text_mode=display.RECORD)
