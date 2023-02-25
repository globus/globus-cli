from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, TextMode, display, formatters

from ._common import SESSION_ENFORCEMENT_FIELD, group_id_arg


@group_id_arg
@command("show")
@LoginManager.requires_login("groups")
def group_show(
    *,
    login_manager: LoginManager,
    group_id: str,
):
    """Show a group definition"""
    groups_client = login_manager.get_groups_client()

    group = groups_client.get_group(group_id, include="my_memberships")

    display(
        group,
        text_mode=TextMode.text_record,
        fields=[
            Field("Name", "name"),
            Field("Description", "description"),
            Field("Type", "group_type"),
            Field("Visibility", "policies.group_visibility"),
            Field("Membership Visibility", "policies.group_members_visibility"),
            SESSION_ENFORCEMENT_FIELD,
            Field("Join Requests Allowed", "policies.join_requests"),
            Field(
                "Signup Fields",
                "policies.signup_fields",
                formatter=formatters.SortedArray,
            ),
            Field("Roles", "my_memberships[].role", formatter=formatters.SortedArray),
        ],
    )
