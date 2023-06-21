import click

from globus_cli.parsing import JSONStringOrFile

input_schema_option = click.option(
    "--input-schema",
    "input_schema",
    type=JSONStringOrFile(),
    help="""
        The JSON input schema that governs the parameters
        used to start the flow.

        The input document may be specified inline, or it may be a path to a JSON file.

        Example: Inline JSON:

        \b
            --input-schema '{"properties": {"src": {"type": "string"}}}'

        Example: Path to JSON file:

        \b
            --input-schema schema.json

        If unspecified, the default is an empty JSON object ('{}').
    """,
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
