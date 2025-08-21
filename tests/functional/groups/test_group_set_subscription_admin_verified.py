import json

import pytest
from globus_sdk._testing import get_last_request, load_response_set


@pytest.mark.parametrize(
    "add_args, expected_value",
    [
        (
            [
                "--subscription-admin-verified-id",
                "e787245d-b5d8-47d1-8ff1-74bc3c5d72f3",
            ],
            "e787245d-b5d8-47d1-8ff1-74bc3c5d72f3",
        ),
        (
            ["--subscription-admin-verified-id", "null"],
            None,
        ),
    ],
)
def test_group_set_subscription_admin_verified(run_line, add_args, expected_value):
    """
    Basic success tests for globus group subscription-verify.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]

    result = run_line(
        ["globus", "group", "set-subscription-admin-verified", group1_id] + add_args
    )

    assert "Group subscription verification updated successfully" in result.output

    last_req = get_last_request()
    sent = json.loads(last_req.body)
    assert sent["subscription_admin_verified_id"] == expected_value
