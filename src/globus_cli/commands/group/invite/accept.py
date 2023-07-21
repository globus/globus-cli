from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import display

from .._common import group_id_arg
from ._common import build_invite_actions, get_invite_formatter


@command("accept", short_help="Accept an invitation")
@group_id_arg
@click.option(
    "--identity",
    type=IdentityType(),
    help="Only accept invitations for a specific identity",
)
@LoginManager.requires_login("groups")
def invite_accept(
    login_manager: LoginManager, *, group_id: uuid.UUID, identity: ParsedIdentity | None
) -> None:
    """
    Accept an invitation to a group

    By default, all invitations to the group are accepted. To restrict this action to
    only specific invitations when there are multiple, use the `--identity` flag.
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()

    actions = build_invite_actions(
        auth_client, groups_client, "accept", group_id, identity
    )
    response = groups_client.batch_membership_action(group_id, actions)
    # if this failed to return at least one accepted user, figure out an error to show
    if not response.get("accept", None):
        try:
            raise ValueError(response["errors"]["accept"][0]["detail"])
        except LookupError:
            raise ValueError("Could not accept invite")

    display(response, text_mode=get_invite_formatter("accept"))
