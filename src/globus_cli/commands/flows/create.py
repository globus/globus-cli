from __future__ import annotations

import typing as t

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, command
from globus_cli.termio import Field, TextMode, display, formatters

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("create", short_help="Create a flow")
@click.argument(
    "title",
    type=str,
)
@click.argument(
    "definition",
    type=JSONStringOrFile(),
    metavar="DEFINITION",
)
@click.option(
    "--input-schema",
    "input_schema",
    type=JSONStringOrFile(),
    help="""
        The JSON input schema that governs the parameters
        used to start the flow.

        The input document may be specified inline,
        or it may be a path to a JSON file, prefixed with "file:".

        Example: Inline JSON:

        \b
            --input_schema '{"properties": {"src": {"type": "string"}}}'

        Example: Path to JSON file:

        \b
            --input_schema file:schema.json

        If unspecified, the default is an empty JSON object ('{}').
    """,
)
@click.option(
    "--subtitle",
    type=str,
    help="A concise summary of the flow's purpose.",
)
@click.option(
    "--description",
    type=str,
    help="A detailed description of the flow's purpose.",
)
@click.option(
    "--administrator",
    "administrators",
    type=str,
    multiple=True,
    help="""
        A principal that may perform administrative operations
        on the flow (e.g., update, delete).

        This option can be specified multiple times
        to create a list of flow administrators.
    """,
)
@click.option(
    "--starter",
    "starters",
    type=str,
    multiple=True,
    help="""
        A principal that may run the flow.

        Use "all_authenticated_users" to allow any authenticated user to run the flow.

        This option can be specified multiple times
        to create a list of flow starters.
    """,
)
@click.option(
    "--viewer",
    "viewers",
    type=str,
    multiple=True,
    help="""
        A principal that may view the flow.

        Use "public" to make the flow visible to everyone.

        This option can be specified multiple times
        to create a list of flow viewers.
    """,
)
@click.option(
    "--keyword",
    "keywords",
    type=str,
    multiple=True,
    help="""
        A term used to help discover this flow when
        browsing and searching.

        This option can be specified multiple times
        to create a list of keywords.
    """,
)
@LoginManager.requires_login("flows")
def create_command(
    login_manager: LoginManager,
    title: str,
    definition: dict,
    input_schema: dict | None | t.Any,
    subtitle: str | None,
    description: str | None,
    administrators: tuple[str],
    starters: tuple[str],
    viewers: tuple[str],
    keywords: tuple[str],
) -> None:
    """
    Create a new flow.

    TITLE is the name of the flow.

    DEFINITION is the JSON document that defines the flow's instructions.
    The definition document may be specified inline,
    or it may be a path to a JSON file, prefixed with "file:".

        Example: Inline JSON:

        \b
            globus flows create 'My Cool Flow' \\
            '{{"StartAt": "a", "States": {{"a": {{"Type": "Pass", "End": true}}}}}}'

        Example: Path to JSON file:

        \b
            globus flows create 'My Other Flow' file:definition.json
    """

    if input_schema is None:
        input_schema = {}

    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()

    res = flows_client.create_flow(
        title=title,
        definition=definition,
        input_schema=input_schema,
        subtitle=subtitle,
        description=description,
        flow_viewers=list(viewers),
        flow_starters=list(starters),
        flow_administrators=list(administrators),
        keywords=list(keywords),
    )

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
