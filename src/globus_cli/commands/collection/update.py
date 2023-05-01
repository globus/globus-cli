from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli import utils
from globus_cli.constants import ExplicitNullType
from globus_cli.endpointish import EntityType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    AnnotatedOption,
    JSONStringOrFile,
    ParsedJSONData,
    collection_id_arg,
    command,
    endpointish_params,
    mutex_option_group,
    nullable_multi_callback,
)
from globus_cli.termio import Field, TextMode, display
from globus_cli.types import ListType

_MULTI_USE_OPTION_STR = "Give this option multiple times in a single command"


class _FullDataField(Field):
    def get_value(self, data):
        return super().get_value(data.full_data)


@command("update", short_help="Update a Collection definition")
@collection_id_arg
@endpointish_params.update(name="collection")
@click.option(
    "--public/--private",
    "public",
    default=None,
    help="Set the collection to be public or private",
)
@click.option(
    "--force-encryption/--no-force-encryption",
    "force_encryption",
    default=None,
    help="When set, all transfers to and from this collection are always encrypted",
)
@click.option(
    "--sharing-restrict-paths",
    type=JSONStringOrFile(null="null"),
    help="Path restrictions for sharing data on guest collections "
    "based on this collection. This option is only usable on Mapped "
    "Collections",
)
@click.option(
    "--allow-guest-collections/--no-allow-guest-collections",
    "allow_guest_collections",
    default=None,
    help=(
        "Allow Guest Collections to be created on this Collection. This option "
        "is only usable on Mapped Collections. If this option is disabled on a "
        "Mapped Collection which already has associated Guest Collections, "
        "those collections will no longer be accessible"
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
        "(requires an endpoint with API v1.8.0)"
    ),
)
@click.option(
    "--domain-name",
    "domain_name",
    default=None,
    help=(
        "DNS host name for the collection (mapped "
        "collections only). This may be either a host name "
        "or a fully-qualified domain name, but if it is the latter "
        "it must be a subdomain of the endpoint's domain"
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
    callback=nullable_multi_callback(""),
    help=(
        "Connector-specific username allowed to create guest collections."
        f"{_MULTI_USE_OPTION_STR} to allow multiple users. "
        'Set a value of "" to clear this'
    ),
    cls=AnnotatedOption,
    type_annotation=t.Union[ListType[str], None, ExplicitNullType],
)
@click.option(
    "--sharing-user-deny",
    "sharing_users_deny",
    multiple=True,
    callback=nullable_multi_callback(""),
    help=(
        "Connector-specific username denied permission to create guest "
        f"collections. {_MULTI_USE_OPTION_STR} to deny multiple users. "
        'Set a value of "" to clear this'
    ),
    cls=AnnotatedOption,
    type_annotation=t.Union[ListType[str], None, ExplicitNullType],
)
@mutex_option_group("--enable-https", "--disable-https")
@LoginManager.requires_login("auth", "transfer")
def collection_update(
    *,
    login_manager: LoginManager,
    collection_id: uuid.UUID,
    display_name: str | None,
    description: str | None | ExplicitNullType,
    info_link: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    contact_email: str | None | ExplicitNullType,
    organization: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    keywords: list[str] | None,
    default_directory: str | None | ExplicitNullType,
    force_encryption: bool | None,
    verify: dict[str, bool],
    public: bool | None,
    sharing_restrict_paths: ParsedJSONData | None | ExplicitNullType,
    allow_guest_collections: bool | None,
    disable_anonymous_writes: bool | None,
    domain_name: str | None,
    enable_https: bool | None,
    user_message: str | None | ExplicitNullType,
    user_message_link: str | None | ExplicitNullType,
    sharing_users_allow: list[str] | None | ExplicitNullType,
    sharing_users_deny: list[str] | None | ExplicitNullType,
) -> None:
    """
    Update a Mapped or Guest Collection
    """
    if isinstance(sharing_restrict_paths, ParsedJSONData) and not isinstance(
        sharing_restrict_paths.data, dict
    ):
        raise click.UsageError("--sharing-restrict-paths must be a JSON object")

    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

    if gcs_client.source_epish.entity_type == EntityType.GCSV5_GUEST:
        doc_class: (
            type[globus_sdk.GuestCollectionDocument]
            | type[globus_sdk.MappedCollectionDocument]
        ) = globus_sdk.GuestCollectionDocument
    else:
        doc_class = globus_sdk.MappedCollectionDocument

    converted_kwargs: dict[str, t.Any] = ExplicitNullType.nullify_dict(
        {
            "display_name": display_name,
            "description": description,
            "info_link": info_link,
            "contact_info": contact_info,
            "contact_email": contact_email,
            "organization": organization,
            "department": department,
            "keywords": keywords,
            "default_directory": default_directory,
            "force_encryption": force_encryption,
            "public": public,
            "sharing_restrict_paths": (
                sharing_restrict_paths.data
                if isinstance(sharing_restrict_paths, ParsedJSONData)
                else sharing_restrict_paths
            ),
            "allow_guest_collections": allow_guest_collections,
            "disable_anonymous_writes": disable_anonymous_writes,
            "domain_name": domain_name,
            "enable_https": enable_https,
            "user_message": user_message,
            "user_message_link": user_message_link,
            "sharing_users_allow": sharing_users_allow,
            "sharing_users_deny": sharing_users_deny,
        }
    )
    converted_kwargs.update(verify)

    # now that any conversions are done, check params against what is (or is not)
    # supported by the document type in use
    doc_params = utils.supported_parameters(doc_class)
    unsupported_params = {
        k for k, v in converted_kwargs.items() if v is not None and k not in doc_params
    }
    if unsupported_params:
        opt_strs = utils.get_current_option_help(filter_names=unsupported_params)
        raise click.UsageError(
            "Use of incompatible options with "
            f"{gcs_client.source_epish.nice_type_name}.\n"
            "The following options are not supported on this collection type:\n  "
            + "\n  ".join(opt_strs)
        )

    doc = doc_class(**converted_kwargs)
    res = gcs_client.update_collection(collection_id, doc)
    display(
        res,
        fields=[_FullDataField("code", "code")],
        text_mode=TextMode.text_record,
    )
