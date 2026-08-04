from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    JSONStringOrFile,
    MutexInfo,
    ParsedJSONData,
    command,
    mutex_option_group,
    web_input_id_arg,
)
from globus_cli.termio import Field, display


@command("respond")
@web_input_id_arg
@click.argument("option_id", metavar="OPTION_ID", type=click.UUID, required=False)
@click.option(
    "--file",
    "file",
    type=JSONStringOrFile(),
    help="""
        A path to a JSON file containing the response value to submit.

        Use this instead of OPTION_ID to respond to a web input which is not a
        "selection" type, or to submit a complex JSON response value.
    """,
)
@mutex_option_group(MutexInfo("OPTION_ID", param="option_id"), "--file")
@LoginManager.requires_login("flows")
def respond_command(
    login_manager: LoginManager,
    *,
    web_input_id: uuid.UUID,
    option_id: uuid.UUID | None,
    file: ParsedJSONData | None,
) -> None:
    """
    Respond to a web input.

    Either OPTION_ID or --file must be provided.

    For "selection" type web inputs, OPTION_ID is the ID of one of the web input's
    available options.
    """
    if option_id is not None:
        value: object = str(option_id)
    elif file is not None:
        value = file.data
    else:
        raise click.UsageError("Either OPTION_ID or '--file' must be provided.")

    flows_client = login_manager.get_flows_client()
    response = flows_client.respond_to_web_input(web_input_id, value=value)

    display(
        response,
        text_mode=display.RECORD,
        fields=[Field("Status", "status")],
    )
