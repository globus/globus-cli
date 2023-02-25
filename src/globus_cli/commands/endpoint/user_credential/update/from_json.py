import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import JSONStringOrFile, command, endpoint_id_arg
from globus_cli.termio import display

from .._common import user_credential_id_arg


@command("from-json", short_help="Update a User Credential with a JSON document")
@endpoint_id_arg
@user_credential_id_arg
@click.argument("user_credential_json", type=JSONStringOrFile())
@LoginManager.requires_login("transfer", "auth")
def from_json(
    *,
    login_manager: LoginManager,
    endpoint_id,
    user_credential_id,
    user_credential_json,
):
    """
    Update a User Credential on an endpoint with a JSON document
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    res = gcs_client.update_user_credential(user_credential_id, user_credential_json)
    display(res, simple_text=res.full_data.get("message"))
