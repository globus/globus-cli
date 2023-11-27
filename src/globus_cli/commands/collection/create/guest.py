from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.collection._common import (
    filter_fields,
    standard_collection_fields,
)
from globus_cli.constants import ExplicitNullType
from globus_cli.endpointish import EntityType
from globus_cli.login_manager import LoginManager, read_well_known_config
from globus_cli.parsing import command, endpointish_params, mutex_option_group
from globus_cli.services.gcs import CustomGCSClient
from globus_cli.termio import TextMode, display


@command("guest", short_help="Create a GCSv5 Guest Collection")
@click.argument("mapped-collection-id", type=click.UUID)
@click.argument("collection-base-path", type=str)
@click.option(
    "--user-credential-id",
    type=click.UUID,
    default=None,
    help="ID identifying a registered local user to associate with the new collection",
)
@click.option(
    "--local-username",
    type=str,
    default=None,
    help=(
        "[Alternative to --user-credential-id] Local username to associate with the new"
        " collection (must match exactly one pre-registered User Credential ID)"
    ),
)
@mutex_option_group("--user-credential-id", "--local-username")
@endpointish_params.create(name="collection")
@click.option(
    "--identity-id",
    default=None,
    help="User who should own the collection (defaults to the current user)",
)
@click.option(
    "--public/--private",
    "public",
    default=True,
    help="Set the collection to be public or private",
)
@click.option(
    "--enable-https/--disable-https",
    "enable_https",
    default=None,
    help=(
        "Explicitly enable or disable  HTTPS support (requires a managed endpoint "
        "with API v1.1.0)"
    ),
)
@mutex_option_group("--enable-https", "--disable-https")
@LoginManager.requires_login("auth", "transfer")
def collection_create_guest(
    login_manager: LoginManager,
    *,
    mapped_collection_id: uuid.UUID,
    collection_base_path: str,
    user_credential_id: uuid.UUID | None,
    local_username: str | None,
    contact_info: str | None | ExplicitNullType,
    contact_email: str | None | ExplicitNullType,
    default_directory: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    description: str | None | ExplicitNullType,
    display_name: str,
    enable_https: bool | None,
    force_encryption: bool | None,
    identity_id: str | None,
    info_link: str | None | ExplicitNullType,
    keywords: list[str] | None,
    public: bool,
    organization: str | None | ExplicitNullType,
    user_message: str | None | ExplicitNullType,
    user_message_link: str | None | ExplicitNullType,
    verify: dict[str, bool],
) -> None:
    """
    Create a GCSv5 Guest Collection
    """
    gcs_client = login_manager.get_gcs_client(
        collection_id=mapped_collection_id,
        include_data_access=True,
        assert_entity_type=(EntityType.GCSV5_MAPPED,),
    )

    if not user_credential_id:
        user_credential_id = _select_user_credential_id(
            gcs_client, mapped_collection_id, local_username, identity_id
        )

    converted_kwargs: dict[str, t.Any] = ExplicitNullType.nullify_dict(
        {
            "collection_base_path": collection_base_path,
            "contact_info": contact_info,
            "contact_email": contact_email,
            "default_directory": default_directory,
            "department": department,
            "description": description,
            "display_name": display_name,
            "enable_https": enable_https,
            "force_encryption": force_encryption,
            "identity_id": identity_id,
            "info_link": info_link,
            "keywords": keywords,
            "mapped_collection_id": mapped_collection_id,
            "public": public,
            "organization": organization,
            "user_credential_id": user_credential_id,
            "user_message": user_message,
            "user_message_link": user_message_link,
        }
    )
    converted_kwargs.update(verify)

    res = gcs_client.create_collection(
        globus_sdk.GuestCollectionDocument(**converted_kwargs)
    )

    fields = standard_collection_fields(login_manager.get_auth_client())
    display(res, text_mode=TextMode.text_record, fields=filter_fields(fields, res))


def _select_user_credential_id(
    gcs_client: CustomGCSClient,
    mapped_collection_id: uuid.UUID,
    local_username: str | None,
    identity_id: str | None,
) -> uuid.UUID:
    """
    In the case that the user didn't specify a user credential id, see if we can select
      one automatically.

    A User Credential is only eligible if it is the only candidate matching the given
      request parameters (which may be omitted).
    """
    mapped_collection = gcs_client.get_collection(mapped_collection_id)
    storage_gateway_id = mapped_collection["storage_gateway_id"]

    if not identity_id:
        user_data = read_well_known_config("auth_user_data", allow_null=False)
        identity_id = user_data["sub"]

    # Grab the list of user credentials which match the endpoint, storage gateway,
    #   identity id, and local username (if specified)
    user_creds = [
        user_cred
        for user_cred in gcs_client.get_user_credential_list(
            storage_gateway=storage_gateway_id
        )
        if (
            user_cred["identity_id"] == identity_id
            and (local_username is None or user_cred.get("username") == local_username)
        )
    ]

    if len(user_creds) > 1:
        # Only instruct them to include --local-username if they didn't already
        local_username_or = "either --local-username or " if not local_username else ""
        raise ValueError(
            "Multiple User Credentials sufficient for Guest Collection Creation. "
            f"Please try again supplying {local_username_or}--user-credential-id."
        )
    if len(user_creds) == 0:
        endpoint_id = gcs_client.source_epish.get_collection_endpoint_id()
        raise ValueError(
            "No User Credentials sufficient for Guest Collection creation.\n\n"
            "To create a Guest Collection, you must first register at least one User "
            "Credential on the requisite 'Endpoint':'Storage Gateway' combo "
            f"('{endpoint_id}':'{storage_gateway_id}').\n"
            "This can be done with: `globus endpoint user-credential create ...`\n"
        )

    return uuid.UUID(user_creds[0]["id"])
