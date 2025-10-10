from __future__ import annotations

import uuid

import click
import globus_sdk
from globus_sdk.services.gcs import UserCredentialDocument

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display

from .._common import user_credential_create_and_update_params


@command("s3")
@endpoint_id_arg
@user_credential_create_and_update_params(create=True)
@click.argument("s3_key_id")
@click.argument("s3_secret_key")
@LoginManager.requires_login("auth", "transfer")
def s3(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    storage_gateway: uuid.UUID,
    globus_identity: str,
    local_username: str,
    s3_key_id: str,
    s3_secret_key: str,
    display_name: str | globus_sdk.MissingType,
) -> None:
    """
    Create a User Credential for an S3 Storage Gateway.
    """
    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    auth_client = login_manager.get_auth_client()

    # TODO: replace with SDK class if one becomes available
    policies = {
        "DATA_TYPE": "s3_user_credential_policies#1.0.0",
        "s3_key_id": s3_key_id,
        "s3_secret_key": s3_secret_key,
    }

    data = UserCredentialDocument(
        storage_gateway_id=storage_gateway,
        identity_id=(
            auth_client.maybe_lookup_identity_id(globus_identity) or globus_sdk.MISSING
        ),
        username=local_username,
        policies=policies,
        display_name=display_name,
    )
    res = gcs_client.create_user_credential(data)

    display(res, simple_text=res.full_data.get("message"))
