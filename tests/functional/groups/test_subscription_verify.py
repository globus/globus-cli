import json

import pytest
from globus_sdk._testing import get_last_request, load_response_set


@pytest.mark.parametrize(
    "add_args, expected_value",
    [
        (
            ["--subscription-id", "e787245d-b5d8-47d1-8ff1-74bc3c5d72f3"],
            "e787245d-b5d8-47d1-8ff1-74bc3c5d72f3",
        ),
        (["--unverify"], None),
    ],
)
def test_group_subscription_verify(run_line, add_args, expected_value):
    """
    Basic success tests for globus group subscription-verify.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]

    result = run_line(["globus", "group", "subscription-verify", group1_id] + add_args)

    assert "Group subscription verification updated successfully" in result.output

    last_req = get_last_request()
    sent = json.loads(last_req.body)
    assert sent["subscription_admin_verified_id"] == expected_value


def test_group_subscription_verify_required_opts(run_line):
    """
    Basic failure test for globus group subscription-verify.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]

    result = run_line(
        f"globus group subscription-verify {group1_id}", assert_exit_code=2
    )

    assert "Either --subscription-id or --unverify must be provided" in result.stderr
