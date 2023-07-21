from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import IdentityType, ParsedIdentity, command
from globus_cli.termio import Field, TextMode, display

from ._common import group_id_arg

JOIN_USER_FIELDS = [
    Field("Group ID", "group_id"),
    Field("User ID", "identity_id"),
    Field("Username", "username"),
]


@command("join", short_help="Join a group")
@group_id_arg
@click.option(
    "--identity",
    type=IdentityType(),
    help="Join as a specific identity, rather than the default",
)
@click.option(
    "--request",
    is_flag=True,
    help="Instead of attempting to join the group directly, create a join "
    "request which can be approved by a group administrator",
)
@LoginManager.requires_login("groups")
def group_join(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
    identity: ParsedIdentity | None,
    request: bool,
) -> None:
    """
    Join a group in which you are not a member.
    """
    auth_client = login_manager.get_auth_client()
    groups_client = login_manager.get_groups_client()

    action = "request_join" if request else "join"

    if identity:
        identity_id = auth_client.maybe_lookup_identity_id(identity.value)
        if not identity_id:
            raise click.UsageError(
                f"Couldn't determine identity from value: {identity}"
            )
    else:
        userinfo = auth_client.oauth2_userinfo()
        identity_id = userinfo["sub"]

    response = groups_client.batch_membership_action(
        group_id, {action: [{"identity_id": identity_id}]}
    )
    # if this failed to return at least one 'join', figure out an error to show
    if not response.get(action, None):
        try:
            raise ValueError(response["errors"][action][0]["detail"])
        except LookupError:
            raise ValueError("Could not join group")

    display(
        response,
        text_mode=TextMode.text_record,
        fields=JOIN_USER_FIELDS,
        response_key=lambda data: data[action][0],
    )
