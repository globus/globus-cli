from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.collection._common import (
    LazyCurrentIdentity,
    filter_fields,
    identity_id_option,
    standard_collection_fields,
)
from globus_cli.constants import ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    JSONStringOrFile,
    MutexInfo,
    ParsedJSONData,
    command,
    endpoint_id_arg,
    endpointish_params,
    mutex_option_group,
)
from globus_cli.termio import display


def _make_multi_use_option_str(s: str) -> str:
    return f"Give this option multiple times to {s}."


def _posix_policy_options_present(params: dict[str, t.Any]) -> bool:
    return bool(
        params["posix_sharing_group_allow"] or params["posix_sharing_group_deny"]
    )


def _posix_staging_policy_options_present(params: dict[str, t.Any]) -> bool:
    return bool(
        params["posix_staging_sharing_group_allow"]
        or params["posix_staging_sharing_group_deny"]
    )


@command("create", short_help="Create a new Mapped Collection.")
@endpoint_id_arg
@endpointish_params.create(name="collection")
@identity_id_option
@click.option(
    "--base-path",
    default="/",
    show_default=True,
    help="The location within the storage gateway where the collection is rooted.",
)
@click.option(
    "--storage-gateway-id",
    help=(
        "The storage gateway ID to host this collection. "
        "If no value is provided but the endpoint has exactly one gateway, "
        "that gateway will be used by default."
    ),
)
@click.option(
    "--sharing-restrict-paths",
    type=JSONStringOrFile(null="null"),
    help=(
        "Path restrictions for sharing data on guest collections "
        "based on this collection."
    ),
)
@click.option(
    "--allow-guest-collections/--no-allow-guest-collections",
    default=None,
    help=(
        "Allow Guest Collections to be created on this Collection. "
        "If this option is later disabled on a Mapped Collection which has associated "
        "Guest Collections, those collections will no longer be accessible."
    ),
)
@click.option(
    "--disable-anonymous-writes/--enable-anonymous-writes",
    default=None,
    help=(
        "Allow anonymous write ACLs on Guest Collections attached to this "
        "Mapped Collection. This option is only usable on non high assurance "
        "Mapped Collections and the setting is inherited by the hosted Guest "
        "Collections. Anonymous write ACLs are enabled by default "
        "(requires an endpoint with API v1.8.0)."
    ),
)
@click.option(
    "--domain-name",
    help=(
        "DNS host name for the collection. This may be either a host name "
        "or a fully-qualified domain name, but if it is the latter "
        "it must be a subdomain of the endpoint's domain."
    ),
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
@click.option(
    "--sharing-user-allow",
    "sharing_users_allow",
    multiple=True,
    help=(
        "Connector-specific username allowed to create guest collections."
        + _make_multi_use_option_str("allow multiple users")
    ),
)
@click.option(
    "--sharing-user-deny",
    "sharing_users_deny",
    multiple=True,
    help=(
        "Connector-specific username denied permission to create guest collections. "
        + _make_multi_use_option_str("deny multiple users")
    ),
)
@click.option(
    "--posix-sharing-group-allow",
    multiple=True,
    help=(
        "POSIX group allowed access to create guest collections "
        + "(POSIX Connector only). "
        + _make_multi_use_option_str("allow multiple groups")
    ),
)
@click.option(
    "--posix-sharing-group-deny",
    multiple=True,
    help=(
        "POSIX group denied permission to create guest collections "
        + "(POSIX Connector only). "
        + _make_multi_use_option_str("deny multiple groups")
    ),
)
@click.option(
    "--google-project-id",
    help=(
        "The Google Cloud Platform project ID which is used by this Collection "
        "(Google Cloud Storage backed Collections only)."
    ),
)
@click.option(
    # POSIX Staging connector (GCS v5.4.10)
    "--posix-staging-sharing-group-allow",
    multiple=True,
    help=(
        "POSIX group allowed access to create guest collections "
        + "(POSIX Staging Connector Only). "
        + _make_multi_use_option_str("allow multiple groups")
    ),
)
@click.option(
    "--posix-staging-sharing-group-deny",
    multiple=True,
    help=(
        "POSIX group denied permission to create guest collections "
        + "(POSIX Staging Connector Only). "
        + _make_multi_use_option_str("deny multiple groups")
    ),
)
@mutex_option_group(
    MutexInfo(
        "--google-project-id",
        # override the default check, which would be `bool(params["google_project_id"])`
        # and would therefore be False for `""`
        present=lambda params: params["google_project_id"] is not None,
    ),
    MutexInfo(
        "--posix-sharing-group-allow/--posix-sharing-group-deny",
        present=_posix_policy_options_present,
    ),
    MutexInfo(
        "--posix-staging-sharing-group-allow/--posix-staging-sharing-group-deny",
        present=_posix_staging_policy_options_present,
    ),
)
@LoginManager.requires_login("auth", "transfer")
def collection_create_mapped(
    login_manager: LoginManager,
    *,
    # positional args
    base_path: str,
    display_name: str,
    endpoint_id: uuid.UUID,
    # options
    allow_guest_collections: bool | None,
    contact_email: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    default_directory: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    description: str | None | ExplicitNullType,
    disable_anonymous_writes: bool | None,
    domain_name: str | None,
    enable_https: bool | None,
    force_encryption: bool | None,
    google_project_id: str | None,
    identity_id: LazyCurrentIdentity,
    info_link: str | None | ExplicitNullType,
    keywords: list[str] | None,
    organization: str | None | ExplicitNullType,
    posix_sharing_group_allow: tuple[str, ...],
    posix_sharing_group_deny: tuple[str, ...],
    posix_staging_sharing_group_allow: tuple[str, ...],
    posix_staging_sharing_group_deny: tuple[str, ...],
    public: bool,
    sharing_restrict_paths: ParsedJSONData | None | ExplicitNullType,
    sharing_users_allow: tuple[str, ...],
    sharing_users_deny: tuple[str, ...],
    storage_gateway_id: str | None,
    user_message: str | None | ExplicitNullType,
    user_message_link: str | None | ExplicitNullType,
    verify: dict[str, bool],
) -> None:
    """
    Create a new Mapped Collection, rooted on some given path within an
    existing Storage Gateway.

    If the '--storage-gateway' option is not used to specify a storage gateway to use
    and there is only one storage gateway on the endpoint, that gateway will be used.
    Otherwise, '--storage-gateway' is required.
    """
    if isinstance(sharing_restrict_paths, ParsedJSONData) and not isinstance(
        sharing_restrict_paths.data, dict
    ):
        raise click.UsageError("--sharing-restrict-paths must be a JSON object")

    gcs_client = login_manager.get_gcs_client(endpoint_id=endpoint_id)
    if storage_gateway_id is None:
        all_gateways = list(gcs_client.get_storage_gateway_list())
        if len(all_gateways) == 0:
            raise click.UsageError(
                "This endpoint does not have any storage gateways. "
                "You must create one before you can create a collection."
            )
        elif len(all_gateways) == 1:
            storage_gateway_id = all_gateways[0]["id"]
        else:
            raise click.UsageError(
                "This endpoint has multiple storage gateways. "
                "You must specify which one to use with the --storage-gateway option."
            )

    policies: globus_sdk.CollectionPolicies | None = None
    if google_project_id is not None:
        policies = globus_sdk.GoogleCloudStorageCollectionPolicies(
            project=google_project_id
        )
    elif posix_sharing_group_allow or posix_sharing_group_deny:
        # Added in 5.4.8 for POSIX connector
        policies = globus_sdk.POSIXCollectionPolicies(
            sharing_groups_allow=posix_sharing_group_allow,
            sharing_groups_deny=posix_sharing_group_deny,
        )
    elif posix_staging_sharing_group_allow or posix_staging_sharing_group_deny:
        # Added in 5.4.10 for POSIX staging connector
        policies = globus_sdk.POSIXStagingCollectionPolicies(
            sharing_groups_allow=posix_staging_sharing_group_allow,
            sharing_groups_deny=posix_staging_sharing_group_deny,
        )

    converted_kwargs: dict[str, t.Any] = ExplicitNullType.nullify_dict(
        {
            # required arguments
            "collection_base_path": base_path,
            "display_name": display_name,
            # options
            "allow_guest_collections": allow_guest_collections,
            "contact_email": contact_email,
            "contact_info": contact_info,
            "default_directory": default_directory,
            "department": department,
            "description": description,
            "disable_anonymous_writes": disable_anonymous_writes,
            "domain_name": domain_name,
            "enable_https": enable_https,
            "force_encryption": force_encryption,
            "identity_id": identity_id.resolve(login_manager),
            "info_link": info_link,
            "keywords": keywords,
            "organization": organization,
            "policies": policies,
            "public": public,
            "sharing_restrict_paths": (
                sharing_restrict_paths.data
                if isinstance(sharing_restrict_paths, ParsedJSONData)
                else sharing_restrict_paths
            ),
            "sharing_users_allow": sharing_users_allow,
            "sharing_users_deny": sharing_users_deny,
            "storage_gateway_id": storage_gateway_id,
            "user_message": user_message,
            "user_message_link": user_message_link,
        }
    )
    converted_kwargs.update(verify)

    collection_doc = globus_sdk.MappedCollectionDocument(
        **converted_kwargs,
    )
    res = gcs_client.create_collection(collection_doc)

    fields = standard_collection_fields(login_manager.get_auth_client())
    display(
        res,
        text_mode=display.RECORD,
        fields=filter_fields(fields, res),
    )
