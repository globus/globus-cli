from __future__ import annotations

import functools
import typing as t

import click

from globus_cli.termio import Field, field_formatters

# cannot do this because it causes immediate imports and ruins the lazy import
# performance gain
#
# MEMBERSHIP_FIELDS = {x.value for x in globus_sdk.GroupRequiredSignupFields}
MEMBERSHIP_FIELDS = {
    "institution",
    "current_project_name",
    "address",
    "city",
    "state",
    "country",
    "address1",
    "address2",
    "zip",
    "phone",
    "department",
    "field_of_science",
}


def group_id_arg(f: t.Callable | None = None):
    if f is None:
        return functools.partial(group_id_arg)
    return click.argument("GROUP_ID")(f)


def parse_roles(res):
    return ",".join(sorted({m["role"] for m in res["my_memberships"]}))


def group_create_and_update_params(
    f: t.Callable | None = None, *, create: bool = False
) -> t.Callable:
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


SESSION_ENFORCEMENT_FIELD = Field(
    "Session Enforcement",
    "enforce_session",
    formatter=field_formatters.FuzzyBoolFieldFormatter(
        true_str="strict", false_str="not strict"
    ),
)
