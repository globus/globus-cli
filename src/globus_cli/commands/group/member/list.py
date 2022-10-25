from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import CommaDelimitedList, command
from globus_cli.termio import FORMAT_TEXT_TABLE, Field, formatted_print

from .._common import MEMBERSHIP_FIELDS, group_id_arg


def _str2field(fieldname: str) -> Field:
    return Field(fieldname.title(), f"membership_fields.{fieldname}")


@group_id_arg
@click.option(
    "--fields",
    help="Additional membership fields to display in the output, as a comma-delimited "
    "string. Has no effect on non-text output.",
    type=CommaDelimitedList(choices=MEMBERSHIP_FIELDS, convert_values=str.lower),
)
@command("list")
@LoginManager.requires_login(LoginManager.GROUPS_RS)
def member_list(
    *,
    login_manager: LoginManager,
    group_id: str,
    fields: list[str] | None,
):
    """List group members"""
    groups_client = login_manager.get_groups_client()

    group = groups_client.get_group(group_id, include="memberships")

    add_fields = []
    if fields:
        add_fields = [_str2field(x) for x in fields]

    formatted_print(
        group,
        text_format=FORMAT_TEXT_TABLE,
        fields=[
            Field("Username", "username"),
            Field("Role", "role"),
            Field("Status", "status"),
        ]
        + add_fields,
        response_key="memberships",
    )
