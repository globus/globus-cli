from __future__ import annotations

import uuid

import click

from globus_cli.commands.flows._common import (
    administrators_option,
    description_option,
    input_schema_option_with_default,
    keywords_option,
    starters_option,
    subtitle_option,
    viewers_option,
)
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, ParsedJSONData, command
from globus_cli.termio import Field, display, formatters
from globus_cli.types import JsonValue

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("create", short_help="Create a flow.")
@click.argument(
    "title",
    type=str,
)
@click.argument(
    "definition",
    type=JSONStringOrFile(),
    metavar="DEFINITION",
)
@input_schema_option_with_default
@subtitle_option
@description_option
@administrators_option
@starters_option
@viewers_option
@keywords_option
@click.option(
    "--run-manager",
    "run_managers",
    type=str,
    multiple=True,
    help="""
        A principal that may manage the flow's runs.
    """,
)
@click.option(
    "--run-monitor",
    "run_monitors",
    type=str,
    multiple=True,
    help="""
        A principal that may monitor the flow's runs.
    """,
)
@click.option(
    "--subscription-id",
    help="Set a subscription_id for the flow, marking it as subscription tier.",
    type=click.UUID,
)
@LoginManager.requires_login("flows")
def create_command(
    login_manager: LoginManager,
    *,
    title: str,
    definition: ParsedJSONData,
    input_schema: ParsedJSONData | None,
    subtitle: str | None,
    description: str | None,
    administrators: tuple[str, ...],
    starters: tuple[str, ...],
    viewers: tuple[str, ...],
    keywords: tuple[str, ...],
    run_managers: tuple[str, ...],
    run_monitors: tuple[str, ...],
    subscription_id: uuid.UUID | None,
) -> None:
    """
    Create a new flow.

    TITLE is the name of the flow.

    DEFINITION is the JSON document that defines the flow's instructions.
    The definition document may be specified inline, or it may be
    a path to a JSON file.

        Example: Inline JSON:

        \b
            globus flows create 'My Cool Flow' \\
            '{{"StartAt": "a", "States": {{"a": {{"Type": "Pass", "End": true}}}}}}'

        Example: Path to JSON file:

        \b
            globus flows create 'My Other Flow' definition.json
    """

    # Ensure that the definition is a JSON object
    if not isinstance(definition.data, dict):
        raise click.UsageError("Flow definition must be a JSON object")
    definition_doc = definition.data

    # Ensure the input schema is a JSON object
    if input_schema is None:
        input_schema_doc: dict[str, JsonValue] = {}
    else:
        if not isinstance(input_schema.data, dict):
            raise click.UsageError("--input-schema must be a JSON object")
        input_schema_doc = input_schema.data

    # Configure clients
    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    res = flows_client.create_flow(
        title=title,
        definition=definition_doc,
        input_schema=input_schema_doc,
        subtitle=subtitle,
        description=description,
        flow_viewers=list(viewers),
        flow_starters=list(starters),
        flow_administrators=list(administrators),
        keywords=list(keywords),
        run_managers=list(run_managers),
        run_monitors=list(run_monitors),
        subscription_id=subscription_id,
    )

    # Configure formatters for principals
    principal_formatter = formatters.auth.PrincipalURNFormatter(auth_client)
    for principal_set_name in ("flow_administrators", "flow_viewers", "flow_starters"):
        for value in res.get(principal_set_name, ()):
            principal_formatter.add_item(value)
    principal_formatter.add_item(res.get("flow_owner"))

    fields = [
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field("Subtitle", "subtitle"),
        Field("Description", "description"),
        Field("Keywords", "keywords", formatter=formatters.ArrayFormatter()),
        Field("Owner", "flow_owner", formatter=principal_formatter),
        Field("Subscription ID", "subscription_id"),
        Field("Created At", "created_at", formatter=formatters.Date),
        Field("Updated At", "updated_at", formatter=formatters.Date),
        Field(
            "Administrators",
            "flow_administrators",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
        Field(
            "Viewers",
            "flow_viewers",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
        Field(
            "Starters",
            "flow_starters",
            formatter=formatters.ArrayFormatter(element_formatter=principal_formatter),
        ),
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
    ]

    display(res, fields=fields, text_mode=display.RECORD)
