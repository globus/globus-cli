from __future__ import annotations

import typing as t

import click

from globus_cli.termio import Field, formatters

C = t.TypeVar("C", bound=t.Union[click.Command, t.Callable])

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


def group_id_arg(f: C) -> C:
    return click.argument("GROUP_ID", type=click.UUID)(f)


SESSION_ENFORCEMENT_FIELD = Field(
    "Session Enforcement",
    "enforce_session",
    formatter=formatters.FuzzyBoolFormatter(true_str="strict", false_str="not strict"),
)
