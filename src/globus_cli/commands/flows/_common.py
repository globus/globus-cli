from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.parsing import OMITTABLE_STRING, JSONStringOrFile

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
    type=OMITTABLE_STRING,
    help="A concise summary of the flow's purpose.",
    default=globus_sdk.MISSING,
)


description_option = click.option(
    "--description",
    type=OMITTABLE_STRING,
    help="A detailed description of the flow's purpose.",
    default=globus_sdk.MISSING,
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


class SubscriptionIdType(click.ParamType):
    name = "SUBSCRIPTION_ID"

    def __init__(self, *, omittable: bool = False) -> None:
        self._omittable = omittable

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | t.Literal["DEFAULT"] | globus_sdk.MissingType:
        if self._omittable and value is globus_sdk.MISSING:
            return globus_sdk.MISSING

        if value.upper() == "DEFAULT":
            return "DEFAULT"
        try:
            return uuid.UUID(value)
        except ValueError:
            self.fail(f"{value} must be either a UUID or 'DEFAULT'", param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        if self._omittable:
            return t.Union[  # type: ignore[return-value]
                uuid.UUID, t.Literal["DEFAULT"], globus_sdk.MissingType
            ]
        return t.Union[uuid.UUID, t.Literal["DEFAULT"]]  # type: ignore[return-value]


subscription_id_option = click.option(
    "--subscription-id",
    "subscription_id",
    type=SubscriptionIdType(omittable=True),
    multiple=False,
    help="""
        A subscription ID to assign to the flow.

        The value may be a UUID or the word "DEFAULT".
    """,
    default=globus_sdk.MISSING,
)
