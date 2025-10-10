import json

import pytest
from globus_sdk.testing import get_last_request, load_response_set


@pytest.mark.parametrize(
    "subscription_id, expected_value",
    [
        (
            "e787245d-b5d8-47d1-8ff1-74bc3c5d72f3",
            "e787245d-b5d8-47d1-8ff1-74bc3c5d72f3",
        ),
        (
            "null",
            None,
        ),
    ],
)
def test_group_set_subscription_admin_verified(
    run_line, subscription_id, expected_value
):
    """
    Basic success tests for globus group subscription-verify.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]

    result = run_line(
        [
            "globus",
            "group",
            "set-subscription-admin-verified",
            group1_id,
            subscription_id,
        ]
    )

    assert "Group subscription verification updated successfully" in result.output

    last_req = get_last_request()
    sent = json.loads(last_req.body)
    assert sent["subscription_admin_verified_id"] == expected_value
