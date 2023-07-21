from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import CommaDelimitedList, command
from globus_cli.termio import Field, TextMode, display

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
@LoginManager.requires_login("groups")
def member_list(
    login_manager: LoginManager,
    *,
    group_id: uuid.UUID,
    fields: list[str] | None,
) -> None:
    """List group members"""
    groups_client = login_manager.get_groups_client()

    group = groups_client.get_group(group_id, include="memberships")

    add_fields = []
    if fields:
        add_fields = [_str2field(x) for x in fields]

    display(
        group,
        text_mode=TextMode.text_table,
        fields=[
            Field("Username", "username"),
            Field("Role", "role"),
            Field("Status", "status"),
        ]
        + add_fields,
        response_key="memberships",
    )
