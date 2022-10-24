from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.principal_resolver import default_identity_id_resolver
from globus_cli.termio import (
    FORMAT_TEXT_RECORD,
    Field,
    field_formatters,
    formatted_print,
)
from globus_cli.types import DATA_CONTAINER_T


def _filter_fields(check_fields: list[Field], data: DATA_CONTAINER_T) -> list[Field]:
    return [f for f in check_fields if f.keyfunc(data) is not None]


def _get_standard_fields() -> list[Field]:
    from globus_cli.services.gcs import ConnectorIdFormatter

    return [
        Field("Display Name", "display_name"),
        Field("Owner", default_identity_id_resolver.field),
        Field("ID", "id"),
        Field("Collection Type", "collection_type"),
        Field("Storage Gateway ID", "storage_gateway_id"),
        Field("Connector", "connector_id", formatter=ConnectorIdFormatter()),
        Field("Allow Guest Collections", "allow_guest_collections"),
        Field("Disable Anonymous Writes", "disable_anonymous_writes"),
        Field("High Assurance", "high_assurance"),
        Field("Authentication Timeout", "authentication_timeout_mins"),
        Field("Multi-factor Authentication", "require_mfa"),
        Field("Manager URL", "manager_url"),
        Field("HTTPS URL", "https_url"),
        Field("TLSFTP URL", "tlsftp_url"),
        Field("Force Encryption", "force_encryption"),
        Field("Public", "public"),
        Field("Organization", "organization"),
        Field("Department", "department"),
        Field("Keywords", "keywords"),
        Field("Description", "description"),
        Field("Contact E-mail", "contact_email"),
        Field("Contact Info", "contact_info"),
        Field("Collection Info Link", "info_link"),
    ]


PRIVATE_FIELDS: list[Field] = [
    Field("Root Path", "root_path"),
    Field("Default Directory", "default_directory"),
    Field(
        "Sharing Path Restrictions",
        "sharing_restrict_paths",
        formatter=field_formatters.SortedJson,
    ),
    Field("Sharing Allowed Users", "sharing_users_allow"),
    Field("Sharing Denied Users", "sharing_users_deny"),
    Field("Sharing Allowed POSIX Groups", "policies.sharing_groups_allow"),
    Field("Sharing Denied POSIX Groups", "policies.sharing_groups_deny"),
]


@command("show", short_help="Show a Collection definition")
@collection_id_arg
@click.option(
    "--include-private-policies",
    is_flag=True,
    help=(
        "Include private policies. Requires administrator role on the endpoint. "
        "Some policy data may only be visible in `--format JSON` output"
    ),
)
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def collection_show(
    *, login_manager: LoginManager, include_private_policies, collection_id
):
    """
    Display a Mapped or Guest Collection
    """
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

    query_params = {}
    fields: list[Field] = _get_standard_fields()

    if include_private_policies:
        query_params["include"] = "private_policies"
        fields += PRIVATE_FIELDS

    res = gcs_client.get_collection(collection_id, query_params=query_params)

    # walk the list of all known fields and reduce the rendering to only look
    # for fields which are actually present
    real_fields = _filter_fields(fields, res)

    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=real_fields,
    )
