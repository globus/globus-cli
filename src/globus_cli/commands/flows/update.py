from __future__ import annotations

import uuid

import click

from globus_cli.commands.flows._common import (
    description_option,
    input_schema_option,
    subtitle_option,
)
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    CommaDelimitedList,
    JSONStringOrFile,
    ParsedJSONData,
    command,
    flow_id_arg,
)
from globus_cli.termio import Field, TextMode, display, formatters
from globus_cli.types import JsonValue

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("update", short_help="Update a flow")
@flow_id_arg
@click.option("--title", type=str, help="The name of the flow.")
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
    type=str,
    help="""
        Assign ownership to your Globus Auth principal ID.

        This option can only be used to take ownership of a flow,
        and your Globus Auth principal ID must already be a flow administrator.

        This option cannot currently be used to assign ownership to an arbitrary user.
    """,
)
@subtitle_option
@description_option
@input_schema_option
@click.option(
    "--administrators",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of flow administrators.

        This must a list of Globus Auth group or identity IDs.
        Passing an empty string will clear any existing flow administrators.
    """,
)
@click.option(
    "--starters",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of flow starters.

        This must a list of Globus Auth group or identity IDs.
        In addition, "all_authenticated_users" is an allowed value.

        Passing an empty string will clear any existing flow starters.
    """,
)
@click.option(
    "--viewers",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of flow viewers.

        This must a list of Globus Auth group or identity IDs.
        In addition, "public" is an allowed value.

        Passing an empty string will clear any existing flow viewers.
    """,
)
@click.option(
    "--keywords",
    type=CommaDelimitedList(),
    help="""
        A comma-separated list of keywords.

        Passing an empty string will clear any existing keywords.
    """,
)
@LoginManager.requires_login("flows")
def update_command(
    flow_id: uuid.UUID,
    login_manager: LoginManager,
    title: str | None,
    definition: ParsedJSONData | None,
    input_schema: ParsedJSONData | None,
    subtitle: str | None,
    description: str | None,
    owner: str | None,
    administrators: list[str] | None,
    starters: list[str] | None,
    viewers: list[str] | None,
    keywords: list[str] | None,
) -> None:
    """
    Update a flow.
    """

    # Ensure that the definition is a JSON object (if provided)
    definition_doc: dict[str, JsonValue] | None = None
    if definition is not None:
        if not isinstance(definition.data, dict):
            raise click.UsageError("Flow definition must be a JSON object")
        definition_doc = definition.data

    # Ensure the input schema is a JSON object (if provided)
    input_schema_doc: dict[str, JsonValue] | None = None
    if input_schema is not None:
        if not isinstance(input_schema.data, dict):
            raise click.UsageError("--input-schema must be a JSON object")
        input_schema_doc = input_schema.data

    # Empty lists (like `xs = []`) will result in erasure of the option.
    # Only pass values if `--x ...` was passed (in which case `xs` will be truthy)
    # or `--no-xs` was specified (in which case `xs` will be an empty list).
    # These conditions are guaranteed because `--x` and `--no-xs` are mutex options.
    prepared_administrators: list[str] | None = None
    if administrators is not None:
        prepared_administrators = list(administrators)
    prepared_starters: list[str] | None = None
    if starters is not None:
        prepared_starters = list(starters)
    prepared_viewers: list[str] | None = None
    if viewers is not None:
        prepared_viewers = list(viewers)
    prepared_keywords: list[str] | None = None
    if keywords is not None:
        prepared_keywords = list(keywords)

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
        flow_administrators=prepared_administrators,
        flow_starters=prepared_starters,
        flow_viewers=prepared_viewers,
        keywords=prepared_keywords,
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
    ]

    display(res, fields=fields, text_mode=TextMode.text_record)
