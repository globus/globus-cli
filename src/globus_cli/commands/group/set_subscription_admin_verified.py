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
@click.option(
    "--subscription-admin-verified-id",
    type=GroupSubscriptionVerifiedIdType(),
    help=(
        "The ID of the subscription to which the group belongs. Use the special value"
        ' "null" to remove subscription verification from the group.'
    ),
    required=True,
)
@LoginManager.requires_login("groups")
def group_set_subscription_admin_verified(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
    subscription_admin_verified_id: uuid.UUID | ExplicitNullType,
) -> None:
    """Mark a group as a subscription-verified resource."""
    groups_client = login_manager.get_groups_client()

    admin_verified_id: str | None = (
        None
        if subscription_admin_verified_id == EXPLICIT_NULL
        else str(subscription_admin_verified_id)
    )

    response = groups_client.set_subscription_admin_verified_id(
        group_id, admin_verified_id
    )

    display(
        response, simple_text="Group subscription verification updated successfully"
    )
