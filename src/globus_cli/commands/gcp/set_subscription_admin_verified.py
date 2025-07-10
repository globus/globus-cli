from __future__ import annotations

import uuid

import click

from globus_cli.endpointish import Endpointish, EntityType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import display


@command(
    "set-subscription-admin-verified",
    short_help="Update a GCP collection's subscription verification status.",
)
@endpoint_id_arg
@click.argument("STATUS", type=bool)
@LoginManager.requires_login("transfer")
def set_collection_subscription_admin_verified(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    status: bool,
) -> None:
    """
    Update a GCP collection's subscription verification status.

    This operation requires membership in a Globus subscription group and has
    authorization requirements which depend upon the caller's roles on the
    subscription group and the collection.

    Subscription administrators can grant or revoke verification on a
    collection that is associated with their subscription without needing an
    administrator role on the collection itself.

    Users with the administrator effective role on the collection can revoke
    verification on a collection, but must still be a subscription administrator
    to grant verification.

    STATUS must be a boolean expressing the subscription admin verified status.
    A value of 'true' grants the status, and a value of 'false' revokes status.
    """
    transfer_client = login_manager.get_transfer_client()
    epish = Endpointish(endpoint_id, transfer_client=transfer_client)
    epish.assert_entity_type(expect_types=(EntityType.GCP_MAPPED, EntityType.GCP_GUEST))

    res = transfer_client.set_subscription_admin_verified(
        endpoint_id,
        status,
    )

    display(res, text_mode=display.RAW, response_key="message")
