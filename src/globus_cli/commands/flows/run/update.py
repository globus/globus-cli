from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import CommaDelimitedList, command, run_id_arg
from globus_cli.termio import Field, TextMode, display, formatters


@command("update", short_help="Update a run")
@run_id_arg
@click.option(
    "--label",
    type=str,
    help="A label to give the run.",
)
@click.option(
    "--managers",
    "run_managers",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of principals that may manage the execution of the run.

        Passing an empty string will clear any existing run managers.
    """,
)
@click.option(
    "--monitors",
    "run_monitors",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of principals that may monitor the execution of the run.

        Passing an empty string will clear any existing run monitors.
    """,
)
@click.option(
    "--tags",
    "tags",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of tags to associate with the run.

        Passing an empty string will clear any existing tags.
    """,
)
@LoginManager.requires_login("flows")
def update_command(
    login_manager: LoginManager,
    run_id: uuid.UUID,
    label: str | None = None,
    run_monitors: list[str] | None = None,
    run_managers: list[str] | None = None,
    tags: list[str] | None = None,
) -> None:
    """
    Update a run.
    """

    flows_client = login_manager.get_flows_client()
    response = flows_client.update_run(
        run_id,
        label=label,
        run_monitors=run_monitors,
        run_managers=run_managers,
        tags=tags,
    )

    auth_client = login_manager.get_auth_client()
    principal_formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    for principal_set_name in ("run_managers", "run_monitors"):
        for value in response.get(principal_set_name, ()):
            principal_formatter.add_item(value)

    fields = [
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        Field("Run ID", "run_id"),
        Field("Run Label", "label"),
        Field(
            "Run Managers",
            "run_managers",
            formatter=formatters.ArrayFormatter(
                delimiter=", ",
                element_formatter=principal_formatter,
            ),
        ),
        Field(
            "Run Monitors",
            "run_monitors",
            formatter=formatters.ArrayFormatter(
                delimiter=", ",
                element_formatter=principal_formatter,
            ),
        ),
        Field(
            "Run Tags",
            "tags",
            formatter=formatters.ArrayFormatter(delimiter=", "),
        ),
        Field("Started At", "start_time", formatter=formatters.Date),
        Field("Completed At", "completion_time", formatter=formatters.Date),
        Field("Status", "status"),
    ]

    display(response, fields=fields, text_mode=TextMode.text_record)
