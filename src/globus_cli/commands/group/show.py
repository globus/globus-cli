from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_RECORD, Field, formatted_print

from ._common import (
    format_session_enforcement,
    group_id_arg,
    parse_join_requests,
    parse_members_visibility,
    parse_roles,
    parse_signup_fields,
    parse_visibility,
)


@group_id_arg
@command("show")
@LoginManager.requires_login(LoginManager.GROUPS_RS)
def group_show(
    *,
    login_manager: LoginManager,
    group_id: str,
):
    """Show a group definition"""
    groups_client = login_manager.get_groups_client()

    group = groups_client.get_group(group_id, include="my_memberships")

    formatted_print(
        group,
        text_format=FORMAT_TEXT_RECORD,
        fields=[
            Field("Name", "name"),
            Field("Description", "description"),
            Field("Type", "group_type"),
            Field("Visibility", parse_visibility),
            Field("Membership Visibility", parse_members_visibility),
            Field("Session Enforcement", format_session_enforcement),
            Field("Join Requests Allowed", parse_join_requests),
            Field("Signup Fields", parse_signup_fields),
            Field("Roles", parse_roles),
        ],
    )
