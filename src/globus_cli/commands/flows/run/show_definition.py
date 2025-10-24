from __future__ import annotations

import uuid

from globus_cli.commands.flows._common import FlowScopeInjector
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import display


@command("show-definition", short_help="Show a run's flow definition and input schema.")
@run_id_arg
@LoginManager.requires_login("auth", "flows", "search")
def show_definition_command(login_manager: LoginManager, *, run_id: uuid.UUID) -> None:
    """
    Show the flow definition and input schema used to start a given run.
    """

    flows_client = login_manager.get_flows_client()

    with FlowScopeInjector(login_manager).for_run(run_id):
        response = flows_client.get_run_definition(run_id)

    display(response, text_mode=display.JSON, sort_json_keys=False)
