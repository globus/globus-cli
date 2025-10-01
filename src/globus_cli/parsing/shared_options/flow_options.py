import click

from globus_cli.parsing import JSONStringOrFile

flow_input_document_option = click.option(
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
