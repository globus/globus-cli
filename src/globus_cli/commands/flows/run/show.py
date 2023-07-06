from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import Field, TextMode, display, formatters


@command("show", short_help="Show a run")
@run_id_arg
@click.option(
    "--include-flow-description",
    is_flag=True,
    default=False,
)
@LoginManager.requires_login("flows")
def show_command(
    login_manager: LoginManager, run_id: uuid.UUID, include_flow_description: bool
) -> None:
    """
    Show a run
    """

    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    response = flows_client.get_run(
        run_id, include_flow_description=include_flow_description or None
    )

    principal_formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    for principal_set_name in ("run_managers", "run_monitors"):
        for value in response.get(principal_set_name, ()):
            principal_formatter.add_item(value)
    principal_formatter.add_item(response.get("run_owner"))

    additional_fields = [
        Field("Flow Subtitle", "flow_description.subtitle"),
        Field("Flow Description", "flow_description.description"),
        Field(
            "Flow Keywords",
            "flow_description.keywords",
            formatter=formatters.ArrayFormatter(delimiter=", "),
        ),
    ]

    fields = [
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        *(additional_fields if include_flow_description else []),
        Field("Run ID", "run_id"),
        Field("Run Label", "label"),
        Field("Run Owner", "run_owner", formatter=principal_formatter),
        Field(
            "Run Managers",
            "run_managers",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
        Field(
            "Run Monitors",
            "run_monitors",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
        Field("Run Tags", "tags", formatter=formatters.ArrayFormatter(delimiter=", ")),
        Field("Started At", "start_time", formatter=formatters.Date),
        Field("Completed At", "completion_time", formatter=formatters.Date),
        Field("Status", "status"),
    ]

    display(response, fields=fields, text_mode=TextMode.text_record)
