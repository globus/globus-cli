from __future__ import annotations

import click
import globus_sdk

from globus_cli.commands.flows._common import input_schema_option
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, ParsedJSONData, command
from globus_cli.termio import Field, display


@command("validate", short_help="Validate a flow definition.")
@click.argument(
    "definition",
    type=JSONStringOrFile(),
    metavar="DEFINITION",
)
@input_schema_option
@LoginManager.requires_login("flows")
def validate_command(
    login_manager: LoginManager,
    *,
    definition: ParsedJSONData,
    input_schema: ParsedJSONData | None,
) -> None:
    """
    Validate a flow definition (BETA).

    DEFINITION is the JSON document that defines the flow's instructions.
    The definition document may be specified inline, or it may be
    a path to a JSON file.

        Example: Inline JSON:

        \b
            globus flows validate \\
            '{{"StartAt": "a", "States": {{"a": {{"Type": "Pass", "End": true}}}}}}'

        Example: Path to JSON file:

        \b
            globus flows validate definition.json
    """
    payload = {}

    # Ensure that the definition is a JSON object
    if not isinstance(definition.data, dict):
        raise click.UsageError("Flow definition must be a JSON object")
    payload["definition"] = definition.data

    # Ensure the input schema, if provided, is a JSON object
    if input_schema is not None:
        if not isinstance(input_schema.data, dict):
            raise click.UsageError("--input-schema must be a JSON object")
        payload["input_schema"] = input_schema.data

    # Configure client
    flows_client = login_manager.get_flows_client()

    res = flows_client.validate_flow(**payload)

    display(
        res,
        text_mode=_validate_flow_output_handler,
    )


def _validate_flow_output_handler(result: globus_sdk.GlobusHTTPResponse) -> None:
    # Discovered scopes output
    analysis_response = result.get("analysis")
    # Beta API: Defend against the case where 'analysis' is no longer returned
    if analysis_response is not None:
        _validate_flow_analysis_output_handler(analysis_response)
        click.echo()

    scopes_response = result.get("scopes")
    # Beta API: Defend against the case where 'scopes' is no longer returned
    if scopes_response is not None:
        _validate_flow_scope_output_handler(scopes_response)


def _validate_flow_scope_output_handler(scopes_response: dict[str, str]) -> None:
    # Always include User and Flow scopes
    scopes_fields = [Field("RunAs", "RunAs"), Field("Scope", "scope")]
    scope_entries = [
        {"RunAs": k, "scope": scope}
        for k, scopes in scopes_response.items()
        for scope in scopes
    ]

    click.echo("Discovered Scopes")
    click.echo("=================")
    if scope_entries:
        display(scope_entries, text_mode=display.TABLE, fields=scopes_fields)
    else:
        click.echo("No scopes discovered")


def _validate_flow_analysis_output_handler(analysis_response: dict[str, str]) -> None:
    # Always include the analysis output
    click.echo("Analysis")
    click.echo("========")
    if count := analysis_response.get("number_of_possibilities"):
        click.echo(f"Possible State Traversals: {count}")
