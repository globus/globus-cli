from __future__ import annotations

import sys

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import CommaDelimitedList, command
from globus_cli.termio import display

from ._common import MEMBERSHIP_FIELDS, group_id_arg

if sys.version_info < (3, 9):
    from typing_extensions import Literal
else:
    from typing import Literal


@click.option(
    "--high-assurance/--no-high-assurance",
    default=None,
    help="Whether the group should enforce high assurance access policies or not.",
)
@click.option(
    "--authentication-timeout",
    type=int,
    help=(
        "Time in seconds before a user must re-authenticate to access a "
        "high assurance group"
    ),
)
@click.option(
    "--visibility",
    type=click.Choice(("authenticated", "private"), case_sensitive=False),
    help=(
        "Determine who can see the group. "
        "If authenticated, all authenticated users can see the group. "
        "If private, only members and managers can see the group."
    ),
)
@click.option(
    "--members-visibility",
    type=click.Choice(("members", "managers"), case_sensitive=False),
    help=(
        "Determine who can see members of the group. "
        "If members, members can see all other members. "
        "If managers, only managers can see members."
    ),
)
@click.option(
    "--join-requests/--no-join-requests",
    default=None,
    help="Flag if request to join the group are allowed or not.",
)
@click.option(
    "--signup-fields",
    type=CommaDelimitedList(choices=MEMBERSHIP_FIELDS, convert_values=str.lower),
    help=(
        "Comma separated list of fields to be required from users applying "
        "for group membership. Pass an empty string to require no fields."
    ),
)
@group_id_arg
@command("set-policies")
@LoginManager.requires_login("groups")
def group_set_policies(
    *,
    login_manager: LoginManager,
    group_id: str,
    high_assurance: bool | None,
    authentication_timeout: int | None,
    visibility: Literal["authenticated", "private"] | None,
    members_visibility: Literal["members", "managers"] | None,
    join_requests: bool | None,
    signup_fields: list[str] | None,
) -> None:
    """Update an existing group's policies"""
    groups_client = login_manager.get_groups_client()

    # get the current state of the group's policies
    existing_policies = groups_client.get_group_policies(group_id)

    data = {
        "is_high_assurance": high_assurance,
        "authentication_assurance_timeout": authentication_timeout,
        "group_visibility": visibility,
        "group_members_visibility": members_visibility,
        "join_requests": join_requests,
        "signup_fields": (signup_fields if signup_fields is not None else None),
    }
    # remove any null values to prevent nulling out unspecified fields
    data = {k: v for k, v in data.items() if v is not None}

    # merge with existing data to include any required unspecified fields
    data = {
        k: (data[k] if k in data else existing_policies[k])
        for k, v in existing_policies.data.items()
    }

    response = groups_client.set_group_policies(group_id, data)
    display(response, simple_text="Group policies updated successfully")
