from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display

from ._common import SUBSCRIPTION_FIELDS


@click.argument("subscription_id", type=click.UUID)
@command("get-subscription-info")
@LoginManager.requires_login("groups")
def group_get_subscription_info(
    login_manager: LoginManager, *, subscription_id: uuid.UUID
) -> None:
    """Show data about a specific Subscription."""
    groups_client = login_manager.get_groups_client()

    subscription_data = groups_client.get_group_by_subscription_id(subscription_id)
    display(
        subscription_data,
        text_mode=display.RECORD,
        fields=[Field("Group ID", "group_id")] + SUBSCRIPTION_FIELDS,
    )
