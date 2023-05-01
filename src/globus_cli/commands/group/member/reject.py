import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import Field, TextMode, display

from .._common import group_id_arg

REJECTED_USER_FIELDS = [
    Field("Group ID", "group_id"),
    Field("Rejected User ID", "identity_id"),
    Field("Rejected User Username", "username"),
]


@command("reject", short_help="Reject a member from a group")
@group_id_arg
@click.argument("user", type=IdentityType())
@LoginManager.requires_login("groups")
def member_reject(
    *, group_id: uuid.UUID, user: ParsedIdentity, login_manager: LoginManager
) -> None:
    """
    Reject a pending member from a group.

    The USER argument may be an identity ID or username (whereas the group must be
    specified with an ID).
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()
    identity_id = auth_client.maybe_lookup_identity_id(user.value)
    if not identity_id:
        raise click.UsageError(f"Couldn't determine identity from user value: {user}")
    actions = {"reject": [{"identity_id": identity_id}]}
    response = groups_client.batch_membership_action(group_id, actions)
    if not response.get("reject", None):
        try:
            raise ValueError(response["errors"]["reject"][0]["detail"])
        except (IndexError, KeyError):
            raise ValueError("Could not reject the user from the group")
    display(
        response,
        text_mode=TextMode.text_record,
        fields=REJECTED_USER_FIELDS,
        response_key=lambda data: data["reject"][0],
    )
