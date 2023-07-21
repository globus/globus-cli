import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import Field, TextMode, display

from .._common import group_id_arg

REMOVED_USER_FIELDS = [
    Field("Group ID", "group_id"),
    Field("Removed User ID", "identity_id"),
    Field("Removed User Username", "username"),
]


@command("remove", short_help="Remove a member from a group")
@group_id_arg
@click.argument("user", type=IdentityType())
@LoginManager.requires_login("groups")
def member_remove(
    login_manager: LoginManager, *, group_id: uuid.UUID, user: ParsedIdentity
) -> None:
    """
    Remove a member from a group.

    The USER argument may be an identity ID or username (whereas the group must be
    specified with an ID).
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()
    identity_id = auth_client.maybe_lookup_identity_id(user.value)
    if not identity_id:
        raise click.UsageError(f"Couldn't determine identity from user value: {user}")
    actions = {"remove": [{"identity_id": identity_id}]}
    response = groups_client.batch_membership_action(group_id, actions)
    if not response.get("remove", None):
        try:
            raise ValueError(response["errors"]["remove"][0]["detail"])
        except (IndexError, KeyError):
            raise ValueError("Could not remove the user from the group")
    display(
        response,
        text_mode=TextMode.text_record,
        fields=REMOVED_USER_FIELDS,
        response_key=lambda data: data["remove"][0],
    )
