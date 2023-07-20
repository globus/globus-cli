from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, ParsedJSONData, command, flow_id_arg
from globus_cli.termio import Field, TextMode, display, formatters
from globus_cli.types import JsonValue

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("start", short_help="Start a flow")
@flow_id_arg
@click.option(
    "--input",
    "input_document",
    type=JSONStringOrFile(),
    help="""
        The JSON input parameters used to start the flow.

        The input document may be specified inline,
        or it may be a path to a JSON file, prefixed with "file:".

        Example: Inline JSON:

        \b
            --input '{"src": "~/source"}'

        Example: Path to JSON file:

        \b
            --input parameters.json

        If unspecified, the default is an empty JSON object ('{}').
    """,
)
@click.option(
    "--label",
    type=str,
    help="A label to give the run.",
)
@click.option(
    "--manager",
    "managers",
    type=str,
    multiple=True,
    help="""
        A principal that may manage the execution of the run.

        This option can be specified multiple times
        to create a list of run managers.
    """,
)
@click.option(
    "--monitor",
    "monitors",
    type=str,
    multiple=True,
    help="""
        A principal that may monitor the execution of the run.

        This option can be specified multiple time
        to create a list of run monitors.
    """,
)
@click.option(
    "--tag",
    "tags",
    type=str,
    multiple=True,
    help="""
        A tag to associate with the run.

        This option can be used multiple times
        to create a list of tags.
    """,
)
@LoginManager.requires_login("flows")
def start_command(
    login_manager: LoginManager,
    flow_id: uuid.UUID,
    input_document: ParsedJSONData | None,
    label: str | None,
    managers: tuple[str, ...],
    monitors: tuple[str, ...],
    tags: tuple[str, ...],
) -> None:
    """
    Start a flow.

    FLOW_ID must be a UUID.
    """

    if input_document is None:
        input_document_json: dict[str, JsonValue] = {}
    else:
        if not isinstance(input_document.data, dict):
            raise click.UsageError("Flow input must be a JSON object")
        input_document_json = input_document.data

    flow_client = login_manager.get_specific_flow_client(flow_id)
    response = flow_client.run_flow(
        body=input_document_json,
        label=label,
        tags=list(tags),
        run_managers=list(managers),
        run_monitors=list(monitors),
    )

    auth_client = login_manager.get_auth_client()
    principal_formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    for principal_set_name in ("run_managers", "run_monitors"):
        for value in response.get(principal_set_name, ()):
            principal_formatter.add_item(value)
    principal_formatter.add_item(response.get("run_owner"))

    fields = [
        Field("Flow ID", "flow_id"),
        Field("Flow title", "flow_title"),
        Field("Run ID", "run_id"),
        Field("Run label", "label"),
        Field(
            "Run owner",
            "run_owner",
            formatter=principal_formatter,
        ),
        Field(
            "Run managers",
            "run_managers",
            formatter=formatters.ArrayFormatter(
                delimiter=", ",
                element_formatter=principal_formatter,
            ),
        ),
        Field(
            "Run monitors",
            "run_monitors",
            formatter=formatters.ArrayFormatter(
                delimiter=", ",
                element_formatter=principal_formatter,
            ),
        ),
        Field(
            "Run tags",
            "tags",
            formatter=formatters.ArrayFormatter(delimiter=", "),
        ),
    ]

    display(response, fields=fields, text_mode=TextMode.text_record)
