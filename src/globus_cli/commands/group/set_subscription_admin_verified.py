from __future__ import annotations

import uuid

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import GroupSubscriptionVerifiedIdType, group_id_arg


@command("set-subscription-admin-verified")
@group_id_arg
@click.argument(
    "SUBSCRIPTION_ID",
    type=GroupSubscriptionVerifiedIdType(),
    metavar="[SUBSCRIPTION_ID|null]",
)
@LoginManager.requires_login("groups")
def group_set_subscription_admin_verified(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
    subscription_id: uuid.UUID | ExplicitNullType,
) -> None:
    """
    Mark a group as a subscription-verified resource.

    SUBSCRIPTION_ID is the ID of the subscription to which this group shall belong,
    or "null" to mark the group as non-verified.
    """
    groups_client = login_manager.get_groups_client()

    admin_verified_id: str | None = (
        None if subscription_id == EXPLICIT_NULL else str(subscription_id)
    )

    response = groups_client.set_subscription_admin_verified(
        group_id, admin_verified_id
    )

    display(
        response, simple_text="Group subscription verification updated successfully"
    )
