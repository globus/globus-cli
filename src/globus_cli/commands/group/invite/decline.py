from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import display

from ._common import build_invite_actions, get_invite_formatter


@command("decline", short_help="Decline an invitation")
@click.argument("group_id", type=click.UUID)
@click.option(
    "--identity",
    type=IdentityType(),
    help="Only decline invitations for a specific identity",
)
@LoginManager.requires_login("groups")
def invite_decline(
    *, group_id: uuid.UUID, identity: ParsedIdentity | None, login_manager: LoginManager
):
    """
    Decline an invitation to a group

    By default, all invitations to the group are declined. To restrict this action to
    only specific invitations when there are multiple, use the `--identity` flag.
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()

    actions = build_invite_actions(
        auth_client, groups_client, "decline", group_id, identity
    )
    response = groups_client.batch_membership_action(group_id, actions)

    # if this failed to return at least one accepted user, figure out an error to show
    if not response.get("decline", None):
        try:
            raise ValueError(response["errors"]["decline"][0]["detail"])
        except LookupError:
            raise ValueError("Could not decline invite")

    display(response, text_mode=get_invite_formatter("decline"))
