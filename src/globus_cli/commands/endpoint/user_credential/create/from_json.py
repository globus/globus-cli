import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    JSONStringOrFile,
    ParsedJSONData,
    command,
    endpoint_id_arg,
)
from globus_cli.termio import display


@command("from-json", short_help="Create a User Credential from a JSON document")
@endpoint_id_arg
@click.argument("user_credential_json", type=JSONStringOrFile())
@LoginManager.requires_login("auth", "transfer")
def from_json(
    *,
    login_manager: LoginManager,
    endpoint_id: uuid.UUID,
    user_credential_json: ParsedJSONData,
) -> None:
    """
    Create a User Credential on an endpoint from a JSON document
    """
    if not isinstance(user_credential_json.data, dict):
        raise click.UsageError("User Credential JSON must be a JSON object")

    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    res = gcs_client.create_user_credential(user_credential_json.data)
    display(res, simple_text=res.full_data.get("message"))
