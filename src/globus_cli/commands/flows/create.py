from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.commands.flows._common import (
    administrators_option,
    description_option,
    input_schema_option_with_default,
    keywords_option,
    starters_option,
    subtitle_option,
    viewers_option,
)
from globus_cli.commands.flows._fields import flow_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, ParsedJSONData, command
from globus_cli.termio import display
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

        This option can be specified multiple times
        to create a list of run managers.
    """,
)
@click.option(
    "--run-monitor",
    "run_monitors",
    type=str,
    multiple=True,
    help="""
        A principal that may monitor the flow's runs.

        This option can be specified multiple times
        to create a list of run monitors.
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
    subtitle: str | globus_sdk.MissingType,
    description: str | globus_sdk.MissingType,
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

    fields = flow_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)
