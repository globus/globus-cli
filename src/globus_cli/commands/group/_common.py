from __future__ import annotations

import functools
from typing import Callable

import click
import globus_sdk

MEMBERSHIP_FIELDS = {x.value for x in globus_sdk.GroupRequiredSignupFields}


def group_id_arg(f: Callable | None = None):
    if f is None:
        return functools.partial(group_id_arg)
    return click.argument("GROUP_ID")(f)


def parse_roles(res):
    return ",".join(sorted({m["role"] for m in res["my_memberships"]}))


def format_session_enforcement(res):
    if res.get("enforce_session"):
        return "strict"
    else:
        return "not strict"


def parse_visibility(res):
    return res["policies"]["group_visibility"]


def parse_members_visibility(res):
    return res["policies"]["group_members_visibility"]


def parse_join_requests(res):
    return res["policies"]["join_requests"]


def parse_signup_fields(res):
    return ",".join(sorted(f for f in res["policies"]["signup_fields"]))


def group_create_and_update_params(
    f: Callable | None = None, *, create: bool = False
) -> Callable:
    """
    Collection of options consumed by group create and update.
    Passing create as True makes any values required for create
    arguments instead of options.
    """
    if f is None:
        return functools.partial(group_create_and_update_params, create=create)

    # name is required for create
    if create:
        f = click.argument("name")(f)
    else:
        f = click.option("--name", help="Name for the group.")(f)

    f = click.option("--description", help="Description for the group.")(f)

    return f
