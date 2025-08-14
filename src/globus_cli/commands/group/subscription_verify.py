from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, mutex_option_group
from globus_cli.termio import display

from ._common import group_id_arg


@command("subscription-verify")
@group_id_arg
@click.option(
    "--subscription-id",
    type=click.UUID,
    help="The ID of the subscription to which the group belongs",
)
@click.option(
    "--unverify",
    is_flag=True,
    help="Flag to remove the subscription admin verification from the group",
)
@mutex_option_group("--subscription-id", "--unverify")
@LoginManager.requires_login("groups")
def group_subscription_verify(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
    subscription_id: uuid.UUID | None,
    unverify: bool,
) -> None:
    """Mark a group as a subscription-verified resource."""
    if not subscription_id and not unverify:
        raise click.UsageError(
            "Either --subscription-id or --unverify must be provided"
        )

    groups_client = login_manager.get_groups_client()

    if unverify:
        subscription_admin_verified_id = None
    else:
        subscription_admin_verified_id = subscription_id

    response = groups_client.set_subscription_admin_verified_id(
        group_id, subscription_admin_verified_id
    )

    display(
        response, simple_text="Group subscription verification updated successfully"
    )
