import sys
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import Field, TextMode, display

from .._common import group_id_arg

if sys.version_info < (3, 9):
    from typing_extensions import Literal
else:
    from typing import Literal

INVITED_USER_FIELDS = [
    Field("Group ID", "group_id"),
    Field("Invited User ID", "identity_id"),
    Field("Invited User Username", "username"),
]


@command("invite", short_help="Invite a user to a group")
@group_id_arg
@click.argument("user", type=IdentityType())
@click.option(
    "--provision-identity",
    is_flag=True,
    help="The invited identity will be provisioned if it does not exist.",
)
@click.option(
    "--role",
    type=click.Choice(("member", "manager", "admin")),
    default="member",
    help="The role for the added user",
    show_default=True,
)
@LoginManager.requires_login("groups")
def member_invite(
    *,
    login_manager: LoginManager,
    group_id: uuid.UUID,
    user: ParsedIdentity,
    provision_identity: bool,
    role: Literal["member", "manager", "admin"],
) -> None:
    """
    Invite a user to a group.

    The USER argument may be an identity ID or username (whereas the group must be
    specified with an ID).
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()
    identity_id = auth_client.maybe_lookup_identity_id(
        user.value, provision=provision_identity
    )
    if not identity_id:
        raise click.UsageError(f"Couldn't determine identity from user value: {user}")
    actions = {"invite": [{"identity_id": identity_id, "role": role}]}
    response = groups_client.batch_membership_action(group_id, actions)
    if not response.get("invite", None):
        try:
            raise ValueError(response["errors"]["invite"][0]["detail"])
        except (IndexError, KeyError):
            raise ValueError("Could not invite the user to the group")
    display(
        response,
        text_mode=TextMode.text_record,
        fields=INVITED_USER_FIELDS,
        response_key=lambda data: data["invite"][0],
    )
