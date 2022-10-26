from __future__ import annotations

import uuid

from globus_sdk.services.gcs import UserCredentialDocument

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display

from .._common import user_credential_create_and_update_params


@command("posix", short_help="Create a User Credential for a POSIX storage gateway")
@endpoint_id_arg
@user_credential_create_and_update_params(create=True)
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def posix(
    *,
    login_manager: LoginManager,
    endpoint_id: uuid.UUID,
    storage_gateway: uuid.UUID,
    globus_identity: str,
    local_username: str,
    display_name: str | None,
):
    """
    Create a User Credential for a POSIX storage gateway
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()

    data = UserCredentialDocument(
        storage_gateway_id=storage_gateway,
        identity_id=auth_client.maybe_lookup_identity_id(globus_identity),
        username=local_username,
        display_name=display_name,
    )
    res = gcs_client.create_user_credential(data)

    display(res, simple_text=res.full_data.get("message"))
