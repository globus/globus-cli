from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType
from globus_cli.termio import Field, formatters
from globus_cli.types import AnyCommand

C = t.TypeVar("C", bound=AnyCommand)

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


SESSION_ENFORCEMENT_FIELD = Field(
    "Session Enforcement",
    "enforce_session",
    formatter=formatters.FuzzyBoolFormatter(true_str="strict", false_str="not strict"),
)

SUBSCRIPTION_FIELDS = [
    Field("Subscription ID", "subscription_id"),
    Field("BAA", "subscription_info.is_baa", formatter=formatters.Bool),
    Field(
        "High Assurance",
        "subscription_info.is_high_assurance",
        formatter=formatters.Bool,
    ),
]

# fields for display of groups with and without a subscription
_BASE_GROUP_RECORD_FIELDS = [
    Field("Name", "name"),
    Field("Description", "description", wrap_enabled=True),
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
    Field(
        "Roles",
        "my_memberships[].role",
        formatter=formatters.SortedArray,
    ),
    Field("Terms and Conditions", "terms_and_conditions", wrap_enabled=True),
]
GROUP_FIELDS = [Field("Group ID", "id")] + _BASE_GROUP_RECORD_FIELDS
GROUP_FIELDS_W_SUBSCRIPTION = (
    [Field("Group ID", "id")] + SUBSCRIPTION_FIELDS + _BASE_GROUP_RECORD_FIELDS
)


def group_id_arg(f: C) -> C:
    return click.argument("GROUP_ID", type=click.UUID)(f)


class GroupSubscriptionVerifiedIdType(click.ParamType):
    name = "TEXT"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | ExplicitNullType:
        if value.lower() == "null":
            return EXPLICIT_NULL

        try:
            return uuid.UUID(value)
        except ValueError:
            msg = (
                f"{value} is invalid. Expected either a UUID or the special value "
                '"null"'
            )
            self.fail(msg, param, ctx)
