from __future__ import annotations

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.termio import Field, formatters
from globus_cli.types import DATA_CONTAINER_T


class LazyCurrentIdentity:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def resolve(self, login_manager: LoginManager) -> str:
        if self._value is None:
            self._value = login_manager.get_current_identity_id()
        return str(self._value)


def _identity_id_callback(
    ctx: click.Context | None,
    param: click.Parameter | None,
    value: str | None,
) -> LazyCurrentIdentity:
    return LazyCurrentIdentity(value)


# NB: this is implemented using a callback rather than a custom type because this lets
# us ensure that we convert the default of `None` to `LazyCurrentIdentity(None)`
# a custom type would still pass a default of `None` unless a callback were specified
identity_id_option = click.option(
    "--identity-id",
    help="User who should own the collection (defaults to the current user)",
    callback=_identity_id_callback,
)


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
