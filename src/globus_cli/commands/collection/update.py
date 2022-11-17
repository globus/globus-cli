from __future__ import annotations

import typing as t

import click
import globus_sdk

from globus_cli import utils
from globus_cli.constants import EXPLICIT_NULL
from globus_cli.endpointish import EntityType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    JSONStringOrFile,
    StringOrNull,
    UrlOrNull,
    collection_id_arg,
    command,
    endpointish_setattr_params,
    mutex_option_group,
    nullable_multi_callback,
)
from globus_cli.termio import Field, TextMode, display


class _FullDataField(Field):
    def get_value(self, data):
        return super().get_value(data.full_data)


def _mkhelp(txt):
    return f"New {txt} the collection"


def collection_update_params(f):
    """
    Collection of options consumed by GCS Collection update

    Usage:

    >>> @collection_create_and_update_params(create=False)
    >>> def command_func(**kwargs):
    >>>     ...
    """
    multi_use_option_str = "Give this option multiple times in a single command"

    f = click.option(
        "--public/--private",
        "public",
        default=None,
        help="Set the collection to be public or private",
    )(f)
    f = click.option(
        "--force-encryption/--no-force-encryption",
        "force_encryption",
        default=None,
        help=(
            "When set, all transfers to and from this collection are "
            "always encrypted"
        ),
    )(f)
    f = click.option(
        "--sharing-restrict-paths",
        type=JSONStringOrFile(null="null"),
        help="Path restrictions for sharing data on guest collections "
        "based on this collection. This option is only usable on Mapped "
        "Collections",
    )(f)
    f = click.option(
        "--allow-guest-collections/--no-allow-guest-collections",
        "allow_guest_collections",
        default=None,
        help=(
            "Allow Guest Collections to be created on this Collection. This option "
            "is only usable on Mapped Collections. If this option is disabled on a "
            "Mapped Collection which already has associated Guest Collections, "
            "those collections will no longer be accessible"
        ),
    )(f)
    f = click.option(
        "--disable-anonymous-writes/--enable-anonymous-writes",
        default=None,
        help=(
            "Allow anonymous write ACLs on Guest Collections attached to this "
            "Mapped Collection. This option is only usable on non high assurance "
            "Mapped Collections and the setting is inherited by the hosted Guest "
            "Collections. Anonymous write ACLs are enabled by default "
            "(requires an endpoint with API v1.8.0)"
        ),
    )(f)
    f = click.option(
        "--domain-name",
        "domain_name",
        default=None,
        help=(
            "DNS host name for the collection (mapped "
            "collections only). This may be either a host name "
            "or a fully-qualified domain name, but if it is the latter "
            "it must be a subdomain of the endpoint's domain"
        ),
    )(f)
    f = click.option(
        "--enable-https",
        is_flag=True,
        help=(
            "Explicitly enable HTTPS supprt (requires a managed endpoint "
            "with API v1.1.0)"
        ),
    )(f)

    f = click.option(
        "--disable-https",
        is_flag=True,
        help=(
            "Explicitly disable HTTPS supprt (requires a managed endpoint "
            "with API v1.1.0)"
        ),
    )(f)
    f = click.option(
        "--user-message",
        help=(
            "A message for clients to display to users when interacting "
            "with this collection"
        ),
        type=StringOrNull(),
    )(f)
    f = click.option(
        "--user-message-link",
        help=(
            "Link to additional messaging for clients to display to users "
            "when interacting with this endpoint, linked to an http or https URL "
            "with this collection"
        ),
        type=UrlOrNull(),
    )(f)
    f = click.option(
        "--sharing-user-allow",
        "sharing_users_allow",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "Connector-specific username allowed to create guest collections."
            f"{multi_use_option_str} to allow multiple users. "
            'Set a value of "" to clear this'
        ),
    )(f)
    f = click.option(
        "--sharing-user-deny",
        "sharing_users_deny",
        multiple=True,
        callback=nullable_multi_callback(""),
        help=(
            "Connector-specific username denied permission to create guest "
            f"collections. {multi_use_option_str} to deny multiple users. "
            'Set a value of "" to clear this'
        ),
    )(f)

    return f


@command("update", short_help="Update a Collection definition")
@collection_id_arg
@endpointish_setattr_params("update", "collection")
@collection_update_params
@mutex_option_group("--enable-https", "--disable-https")
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def collection_update(
    *,
    login_manager: LoginManager,
    collection_id,
    display_name: str | None,
    description: str | None,
    info_link: str | None,
    contact_info: str | None,
    contact_email: str | None,
    organization: str | None,
    department: str | None,
    keywords: str | None,
    default_directory: str | None,
    force_encryption: bool | None,
    verify: dict[str, bool],
    **kwargs,
):
    """
    Update a Mapped or Guest Collection
    """
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

    if gcs_client.source_epish.entity_type == EntityType.GCSV5_GUEST:
        doc_class: (
            type[globus_sdk.GuestCollectionDocument]
            | type[globus_sdk.MappedCollectionDocument]
        ) = globus_sdk.GuestCollectionDocument
    else:
        doc_class = globus_sdk.MappedCollectionDocument

    # convert keyword args as follows:
    # - filter out Nones
    # - pass through EXPLICIT_NULL as None
    converted_kwargs: dict[str, t.Any] = {
        k: (v if v != EXPLICIT_NULL else None)
        for k, v in {
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
            **kwargs,
        }.items()
        if v is not None
    }

    if converted_kwargs.get("enable_https") is False:
        converted_kwargs.pop("enable_https")
    if converted_kwargs.pop("disable_https", None):
        converted_kwargs["enable_https"] = False

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
