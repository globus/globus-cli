import json
import uuid

import pytest
from globus_sdk.testing import get_last_request, load_response_set


@pytest.mark.parametrize(
    "add_args, payload_contains",
    (
        (("--name", "New Name"), {"name": "New Name"}),
        (("--description", "New Description"), {"description": "New Description"}),
        (
            ("--terms-and-conditions", "New Terms and Conditions"),
            {"terms_and_conditions": "New Terms and Conditions"},
        ),
        (
            ("--subscription-admin-verified-id", "null"),
            {"subscription_admin_verified_id": None},
        ),
        (
            (
                "--name",
                "New Name",
                "--description",
                "New Description",
                "--terms-and-conditions",
                "New Terms and Conditions",
                "--subscription-admin-verified-id",
                "null",
            ),
            {
                "description": "New Description",
                "name": "New Name",
                "terms_and_conditions": "New Terms and Conditions",
                "subscription_admin_verified_id": None,
            },
        ),
    ),
)
def test_group_update(run_line, add_args, payload_contains):
    """
    Basic success test for globus group update
    Confirms existing values are included in the put document when
    not specified by options
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]
    group1_name = meta["group1_name"]
    group1_description = meta["group1_description"]
    group1_subscription_admin_verified_id = meta[
        "group1_subscription_admin_verified_id"
    ]

    # update name
    result = run_line(("globus", "group", "update", group1_id) + add_args)
    assert "Group updated successfully" in result.output

    # confirm that 'name' and 'description' are both always sent,
    # either with the new values or with their pre-existing values
    last_req = get_last_request()
    sent = json.loads(last_req.body)
    if "name" in payload_contains:
        assert sent["name"] == payload_contains["name"]
    else:
        assert sent["name"] == group1_name
    if "description" in payload_contains:
        assert sent["description"] == payload_contains["description"]
    else:
        assert sent["description"] == group1_description
    if "subscription_admin_verified_id" in payload_contains:
        assert sent["subscription_admin_verified_id"] is None
    else:
        assert (
            sent["subscription_admin_verified_id"]
            == group1_subscription_admin_verified_id
        )


def test_group_set_subscription_admin_verified_id(run_line):
    """
    Basic failure test for subscription_admin_verified_id.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]
    new_id = str(uuid.uuid4())

    result = run_line(
        f"globus group update {group1_id} --subscription-admin-verified-id {new_id}",
        assert_exit_code=2,
    )

    assert (
        "To set the `subscription_admin_verified_id` to a new, non-null value, use "
        "`globus group set-subscription-admin-verified`"
    ) in result.stderr
