from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import OMITTABLE_STRING, CommaDelimitedList, command, run_id_arg
from globus_cli.termio import Field, display, formatters


@command("update")
@run_id_arg
@click.option(
    "--label",
    help="A label to give the run.",
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option(
    "--managers",
    "run_managers",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of principals that may manage the execution of the run.

        Passing an empty string will clear any existing run managers.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--monitors",
    "run_monitors",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of principals that may monitor the execution of the run.

        Passing an empty string will clear any existing run monitors.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--tags",
    "tags",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of tags to associate with the run.

        Passing an empty string will clear any existing tags.
    """,
    default=globus_sdk.MISSING,
)
@LoginManager.requires_login("flows")
def update_command(
    login_manager: LoginManager,
    *,
    run_id: uuid.UUID,
    label: str | globus_sdk.MissingType,
    run_monitors: list[str] | globus_sdk.MissingType,
    run_managers: list[str] | globus_sdk.MissingType,
    tags: list[str] | globus_sdk.MissingType,
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

    display(response, fields=fields, text_mode=display.RECORD)
