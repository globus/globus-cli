import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.principal_resolver import default_identity_id_resolver
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print

from ._common import user_credential_id_arg

STANDARD_FIELDS = [
    ("ID", "id"),
    ("Display Name", "display_name"),
    ("Globus Identity", default_identity_id_resolver.field),
    ("Local Username", "username"),
    (
        "Connector",
        lambda res: globus_sdk.GCSClient.connector_id_to_name(res["connector_id"]),
    ),
    ("Invalid", "invalid"),
    ("Provisioned", "provisioned"),
    ("Policies", "policies"),  # TODO: dict formatting?
]


@command("show", short_help="Show a specific User Credential on an Endpoint")
@endpoint_id_arg
@user_credential_id_arg
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def user_credential_show(
    *,
    login_manager: LoginManager,
    endpoint_id,
    user_credential_id,
):
    """
    Show a specific User Credential on a given Globus Connect Server v5 Endpoint
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)

    res = gcs_client.get_user_credential(user_credential_id)
    formatted_print(res, text_format=FORMAT_TEXT_RECORD, fields=STANDARD_FIELDS)
