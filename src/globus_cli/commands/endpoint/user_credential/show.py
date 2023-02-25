import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import Field, TextMode, display, formatters

from ._common import user_credential_id_arg


@command("show", short_help="Show a specific User Credential on an Endpoint")
@endpoint_id_arg
@user_credential_id_arg
@LoginManager.requires_login("transfer", "auth")
def user_credential_show(
    *,
    login_manager: LoginManager,
    endpoint_id: uuid.UUID,
    user_credential_id: uuid.UUID,
):
    """
    Show a specific User Credential on a given Globus Connect Server v5 Endpoint
    """
    from globus_cli.services.gcs import ConnectorIdFormatter

    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()

    fields = [
        Field("ID", "id"),
        Field("Display Name", "display_name"),
        Field(
            "Globus Identity",
            "identity_id",
            formatter=formatters.auth.IdentityIDFormatter(auth_client),
        ),
        Field("Local Username", "username"),
        Field("Connector", "connector_id", formatter=ConnectorIdFormatter()),
        Field("Invalid", "invalid"),
        Field("Provisioned", "provisioned"),
        Field("Policies", "policies", formatter=formatters.SortedJson),
    ]

    res = gcs_client.get_user_credential(user_credential_id)
    display(res, text_mode=TextMode.text_record, fields=fields)
