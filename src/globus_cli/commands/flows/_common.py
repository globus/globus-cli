from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.parsing import JSONStringOrFile

_input_schema_helptext = """
        The JSON input schema that governs the parameters
        used to start the flow.

        The input document may be specified inline, or it may be a path to a JSON file.

        Example: Inline JSON:

        \b
            --input-schema '{"properties": {"src": {"type": "string"}}}'

        Example: Path to JSON file:

        \b
            --input-schema schema.json
    """

input_schema_option = click.option(
    "--input-schema",
    "input_schema",
    type=JSONStringOrFile(),
    help=_input_schema_helptext,
)

input_schema_option_with_default = click.option(
    "--input-schema",
    "input_schema",
    type=JSONStringOrFile(),
    help=_input_schema_helptext
    + "\n    If unspecified, the default is an empty JSON object ('{}').",
)

subtitle_option = click.option(
    "--subtitle",
    type=str,
    help="A concise summary of the flow's purpose.",
)


description_option = click.option(
    "--description",
    type=str,
    help="A detailed description of the flow's purpose.",
)


administrators_option = click.option(
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


starters_option = click.option(
    "--starter",
    "starters",
    type=str,
    multiple=True,
    help="""
        A principal that may start a new run of the flow.

        Use "all_authenticated_users" to allow any authenticated user
        to start a new run of the flow.

        This option can be specified multiple times
        to create a list of flow starters.
    """,
)


viewers_option = click.option(
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


keywords_option = click.option(
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

run_managers_option = click.option(
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

run_monitors_option = click.option(
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


class SubscriptionIdType(click.ParamType):
    name = "SUBSCRIPTION_ID"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | t.Literal["DEFAULT"]:
        if value.upper() == "DEFAULT":
            return "DEFAULT"
        try:
            return uuid.UUID(value)
        except ValueError:
            self.fail(f"{value} must be either a UUID or 'DEFAULT'", param, ctx)


subscription_id_option = click.option(
    "--subscription-id",
    "subscription_id",
    type=SubscriptionIdType(),
    multiple=False,
    help="""
        A subscription ID to assign to the flow.

        The value may be a UUID or the word "DEFAULT".
    """,
)
