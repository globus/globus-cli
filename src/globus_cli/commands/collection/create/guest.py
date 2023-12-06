from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk
import globus_sdk.experimental.auth_requirements_error

from globus_cli.commands.collection._common import (
    filter_fields,
    standard_collection_fields,
)
from globus_cli.constants import ExplicitNullType
from globus_cli.endpointish import EntityType
from globus_cli.login_manager import (
    LoginManager,
    MissingLoginError,
    read_well_known_config,
)
from globus_cli.login_manager.context import LoginContext
from globus_cli.parsing import command, endpointish_params, mutex_option_group
from globus_cli.services.gcs import CustomGCSClient
from globus_cli.termio import TextMode, display


@command("guest", short_help="Create a GCSv5 Guest Collection")
@click.argument("MAPPED_COLLECTION_ID", type=click.UUID)
@click.argument("COLLECTION_BASE_PATH", type=str)
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
    Create a GCSv5 Guest Collection.

    Create a new guest collection, named DISPLAY_NAME, as a child of
    MAPPED_COLLECTION_ID. This new guest collection's file system must be rooted at
    COLLECTION_BASE_PATH, a file path on the mapped collection.
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

    try:
        res = gcs_client.create_collection(
            globus_sdk.GuestCollectionDocument(**converted_kwargs)
        )
    except globus_sdk.GCSAPIError as e:
        # Detect session timeouts related to HA collections.
        # This is a hacky workaround until we have better GARE support across the CLI.
        if _is_session_timeout_error(e):
            endpoint_id = gcs_client.source_epish.get_collection_endpoint_id()
            login_gcs_id = endpoint_id
            if gcs_client.source_epish.requires_data_access_scope:
                login_gcs_id = f"{endpoint_id}:{mapped_collection_id}"
            context = LoginContext(
                error_message="Session timeout detected; Re-authentication required.",
                login_command=f"globus login --gcs {login_gcs_id} --force",
            )
            raise MissingLoginError([endpoint_id], context=context)
        raise

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
            "More than one gcs user credential valid for creation. "
            f"Please specify which user credential you'd like to use with "
            f"{local_username_or}--user-credential-id."
        )
    if len(user_creds) == 0:
        endpoint_id = gcs_client.source_epish.get_collection_endpoint_id()
        raise ValueError(
            "No valid gcs user credentials discovered.\n\n"
            "Please first create a user credential on this endpoint:\n\n"
            f"\tCommand: globus endpoint user-credential create ...\n"
            f"\tEndpoint ID: {endpoint_id}\n"
            f"\tStorage Gateway ID: {storage_gateway_id}\n"
        )

    return uuid.UUID(user_creds[0]["id"])


def _is_session_timeout_error(e: globus_sdk.GCSAPIError) -> bool:
    """
    Detect session timeouts related to HA collections.
    This is a hacky workaround until we have better GARE support across the CLI.
    """
    detail_type = getattr(e, "detail", {}).get("DATA_TYPE")
    return (
        e.http_status == 403
        and isinstance(detail_type, str)
        and detail_type.startswith("authentication_timeout")
    )
