from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, field_formatters, formatted_print

from ._common import SESSION_ENFORCEMENT_FIELD


@command("list", short_help="List groups you belong to")
@LoginManager.requires_login(LoginManager.GROUPS_RS)
def group_list(*, login_manager: LoginManager):
    """List all groups for the current user"""
    groups_client = login_manager.get_groups_client()

    groups = groups_client.get_my_groups()

    formatted_print(
        groups,
        fields=[
            Field("Group ID", "id"),
            Field("Name", "name"),
            Field("Type", "group_type"),
            SESSION_ENFORCEMENT_FIELD,
            Field(
                "Roles", "my_memberships[].role", formatter=field_formatters.SortedArray
            ),
        ],
    )
