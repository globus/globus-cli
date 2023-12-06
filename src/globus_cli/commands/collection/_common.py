from __future__ import annotations

import globus_sdk

from globus_cli.termio import Field, formatters
from globus_cli.types import DATA_CONTAINER_T


def filter_fields(check_fields: list[Field], data: DATA_CONTAINER_T) -> list[Field]:
    return [f for f in check_fields if f.get_value(data) is not None]


def standard_collection_fields(auth_client: globus_sdk.AuthClient) -> list[Field]:
    from globus_cli.services.gcs import ConnectorIdFormatter

    return [
        Field("Display Name", "display_name"),
        Field(
            "Owner",
            "identity_id",
            formatter=formatters.auth.IdentityIDFormatter(auth_client),
        ),
        Field("ID", "id"),
        Field("Collection Type", "collection_type"),
        Field("Mapped Collection ID", "mapped_collection_id"),
        Field("User Credential ID", "user_credential_id"),
        Field("Storage Gateway ID", "storage_gateway_id"),
        Field("Connector", "connector_id", formatter=ConnectorIdFormatter()),
        Field("Allow Guest Collections", "allow_guest_collections"),
        Field("Disable Anonymous Writes", "disable_anonymous_writes"),
        Field("High Assurance", "high_assurance"),
        Field("Authentication Timeout (Minutes)", "authentication_timeout_mins"),
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
        Field("User Message", "user_message"),
        Field("User Message Link", "user_message_link"),
    ]
