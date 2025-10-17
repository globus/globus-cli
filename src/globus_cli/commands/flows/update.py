from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.flows._common import (
    description_option,
    input_schema_option_with_default,
    subscription_id_option,
    subtitle_option,
)
from globus_cli.commands.flows._fields import flow_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    OMITTABLE_STRING,
    CommaDelimitedList,
    JSONStringOrFile,
    ParsedJSONData,
    command,
    flow_id_arg,
)
from globus_cli.termio import display
from globus_cli.types import JsonValue

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("update", short_help="Update a flow.")
@flow_id_arg
@click.option(
    "--title",
    help="The name of the flow.",
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option(
    "--definition",
    type=JSONStringOrFile(),
    help="""
        The JSON document that defines the flow's instructions.

        The definition document may be specified inline, or it may be
        a path to a JSON file.

            Example: Inline JSON:

            \b
            --definition '{{"StartAt": "a", "States": {{"a": {{"Type": "Pass", "End": true}}}}}}'

            Example: Path to JSON file:

            \b
            --definition definition.json
    """,  # noqa: E501
)
@click.option(
    "--owner",
    help="""
        Assign ownership to your Globus Auth principal ID.

        This option can only be used to take ownership of a flow,
        and your Globus Auth principal ID must already be a flow administrator.

        This option cannot currently be used to assign ownership to an arbitrary user.
    """,
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@subtitle_option
@description_option
@input_schema_option_with_default
@click.option(
    "--administrators",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of flow administrators.

        This must a list of Globus Auth group or identity IDs.
        Passing an empty string will clear any existing flow administrators.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--starters",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of flow starters.

        This must a list of Globus Auth group or identity IDs.
        In addition, "all_authenticated_users" is an allowed value.

        Passing an empty string will clear any existing flow starters.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--viewers",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of flow viewers.

        This must a list of Globus Auth group or identity IDs.
        In addition, "public" is an allowed value.

        Passing an empty string will clear any existing flow viewers.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--run-managers",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of flow run managers.

        This must a list of Globus Auth group or identity IDs.

        Passing an empty string will clear any existing flow run managers.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--run-monitors",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of flow run monitors.

        This must a list of Globus Auth group or identity IDs.

        Passing an empty string will clear any existing flow run monitors.
    """,
    default=globus_sdk.MISSING,
)
@click.option(
    "--keywords",
    type=CommaDelimitedList(omittable=True),
    help="""
        A comma-separated list of keywords.

        Passing an empty string will clear any existing keywords.
    """,
    default=globus_sdk.MISSING,
)
@subscription_id_option
@LoginManager.requires_login("flows")
def update_command(
    login_manager: LoginManager,
    *,
    flow_id: uuid.UUID,
    title: str | globus_sdk.MissingType,
    definition: ParsedJSONData | None,
    input_schema: ParsedJSONData | None,
    subtitle: str | globus_sdk.MissingType,
    description: str | globus_sdk.MissingType,
    owner: str | globus_sdk.MissingType,
    administrators: list[str] | globus_sdk.MissingType,
    starters: list[str] | globus_sdk.MissingType,
    viewers: list[str] | globus_sdk.MissingType,
    run_managers: list[str] | globus_sdk.MissingType,
    run_monitors: list[str] | globus_sdk.MissingType,
    keywords: list[str] | globus_sdk.MissingType,
    subscription_id: uuid.UUID | t.Literal["DEFAULT"] | globus_sdk.MissingType,
) -> None:
    """
    Update a flow.
    """

    # Ensure that the definition is a JSON object (if provided)
    definition_doc: dict[str, JsonValue] | globus_sdk.MissingType = globus_sdk.MISSING
    if definition is not None:
        if not isinstance(definition.data, dict):
            raise click.UsageError("Flow definition must be a JSON object")
        definition_doc = definition.data

    # Ensure the input schema is a JSON object (if provided)
    input_schema_doc: dict[str, JsonValue] | globus_sdk.MissingType = globus_sdk.MISSING
    if input_schema is not None:
        if not isinstance(input_schema.data, dict):
            raise click.UsageError("--input-schema must be a JSON object")
        input_schema_doc = input_schema.data

    # Configure clients
    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    res = flows_client.update_flow(
        flow_id,
        title=title,
        definition=definition_doc,
        input_schema=input_schema_doc,
        subtitle=subtitle,
        description=description,
        flow_owner=owner,
        flow_administrators=administrators,
        flow_starters=starters,
        flow_viewers=viewers,
        run_managers=run_managers,
        run_monitors=run_monitors,
        keywords=keywords,
        subscription_id=subscription_id or globus_sdk.MISSING,
    )

    fields = flow_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)
