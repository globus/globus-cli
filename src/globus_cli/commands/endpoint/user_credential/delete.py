from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display

from ._common import user_credential_id_arg


@command("delete", short_help="Delete a specific User Credential on an Endpoint")
@endpoint_id_arg
@user_credential_id_arg
@LoginManager.requires_login("auth", "transfer")
def user_credential_delete(
    *,
    login_manager: LoginManager,
    endpoint_id,
    user_credential_id,
):
    """
    Delete a specific User Credential on a given Globus Connect Server v5 Endpoint
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    res = gcs_client.delete_user_credential(user_credential_id)

    display(res, simple_text=res.data.get("message"))
