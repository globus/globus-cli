import json
import re
import uuid

import pytest
from globus_sdk.testing import load_response, register_response_set


@pytest.fixture(autouse=True, scope="session")
def _register_responses():
    group_id = str(uuid.uuid4())
    group_name = "My Subscription Group"
    group_description = "One group to rule them all."

    user_identity_id = str(uuid.uuid4())

    subscription_id = str(uuid.uuid4())
    connector_id = str(uuid.uuid4())

    register_response_set(
        "cli.group_get_by_subscription",
        {
            "default": {
                "service": "groups",
                "path": f"/v2/subscription_info/{subscription_id}",
                "json": {
                    "group_id": group_id,
                    "subscription_id": subscription_id,
                    "subscription_info": {
                        "connectors": {
                            connector_id: {
                                "is_baa": False,
                                "is_ha": True,
                            }
                        },
                        "is_baa": False,
                        "is_high_assurance": False,
                    },
                },
            },
            "get_group": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {
                    "id": group_id,
                    "subscription_id": subscription_id,
                    "subscription_info": {
                        "connectors": {
                            connector_id: {
                                "is_baa": False,
                                "is_ha": True,
                            }
                        },
                        "is_baa": False,
                        "is_high_assurance": False,
                    },
                    "name": group_name,
                    "description": group_description,
                    "group_type": "regular",
                    "enforce_session": False,
                    "my_memberships": [
                        {
                            "group_id": group_id,
                            "identity_id": user_identity_id,
                            "username": "jurt@example.com",
                            "role": "admin",
                        }
                    ],
                    "policies": {
                        "authentication_assurance_timeout": 28800,
                        "group_members_visibility": "managers",
                        "group_visibility": "private",
                        "is_high_assurance": False,
                        "join_requests": False,
                        "signup_fields": [],
                    },
                },
            },
            "get_group_not_visible": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {"message": "forbidden!"},
                "status": 403,
            },
            "get_group_fails": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {"message": "boom!"},
                "status": 409,
                "metadata": {"message": "boom!"},
            },
        },
        metadata={
            "group_id": group_id,
            "group_name": group_name,
            "group_description": group_description,
            "user_identity_id": user_identity_id,
            "subscription_id": subscription_id,
            "connector_id": connector_id,
        },
    )


@pytest.mark.parametrize("group_visible", (True, False))
def test_group_get_by_subscription_json_output(run_line, group_visible):
    """
    JSON output shows the subscription info regardless of
    whether or not the group is visible
    """
    meta = load_response("cli.group_get_by_subscription").metadata
    if group_visible:
        load_response("cli.group_get_by_subscription", case="get_group")
    else:
        load_response("cli.group_get_by_subscription", case="get_group_not_visible")

    result = run_line(
        f"globus group get-by-subscription -Fjson {meta['subscription_id']}"
    )

    data = json.loads(result.stdout)
    assert data["group_id"] == meta["group_id"]
    assert data["subscription_id"] == meta["subscription_id"]


def test_group_get_by_subscription_text(run_line):
    meta = load_response("cli.group_get_by_subscription").metadata
    load_response("cli.group_get_by_subscription", case="get_group")

    run_line(
        f"globus group get-by-subscription {meta['subscription_id']}",
        search_stdout=[
            ("Group ID", meta["group_id"]),
            ("Name", meta["group_name"]),
            ("Description", meta["group_description"]),
        ],
    )


@pytest.mark.parametrize("output_format", ("text", "json", "unix"))
def test_group_get_by_subscription_non_visible_group(
    run_line, monkeypatch, output_format
):
    """
    Test that when the group is not visible:
    - text output shows just the group ID
    - a warning/hint will be shown in text mode (if interactive)
    - the hint will not be shown in non-text modes
    """
    # force interactive and patch detection methods to get command hints to print
    monkeypatch.setenv("GLOBUS_CLI_INTERACTIVE", "1")
    monkeypatch.setattr("globus_cli.termio.err_is_terminal", lambda: True)
    monkeypatch.setattr("globus_cli.termio.out_is_terminal", lambda: True)

    meta = load_response("cli.group_get_by_subscription").metadata
    load_response("cli.group_get_by_subscription", case="get_group_not_visible")

    result = run_line(
        f"globus group get-by-subscription {meta['subscription_id']} -F{output_format}",
    )
    # in text output, only the subscription info fields are shown and the hint gets
    # printed to stderr
    if output_format == "text":
        assert re.match(
            r"The Group for this Subscription is not visible to you\.", result.stderr
        )
        result_lines = result.stdout.splitlines()
        assert len(result_lines) == 4
        assert re.match(r"Group ID:\s+" + re.escape(meta["group_id"]), result_lines[0])
        assert {r.partition(":")[0] for r in result_lines} == {
            "Group ID",
            "Subscription ID",
            "BAA",
            "High Assurance",
        }
    # for non-text output, there is no such hint
    else:
        assert result.stderr == ""


def test_group_get_by_subscription_errors_if_unexpected_error_on_group_lookup(run_line):
    """
    We're handling exceptions in the group lookup; ensure that we don't capture things
    like 500s, 502s, 409s, etc
    """
    meta = load_response("cli.group_get_by_subscription").metadata
    error_meta = load_response(
        "cli.group_get_by_subscription", case="get_group_fails"
    ).metadata
    expect_error = error_meta["message"]

    result = run_line(
        f"globus group get-by-subscription {meta['subscription_id']}",
        assert_exit_code=1,
    )
    assert expect_error in result.stderr


def test_group_get_by_subscription_skips_group_lookup_for_json_output(run_line):
    """
    Assume the lookup is broken in some way.
    Ensure that `--format json` does not hit that error at all.
    """
    meta = load_response("cli.group_get_by_subscription").metadata
    load_response("cli.group_get_by_subscription", case="get_group_fails")

    # ensure success
    run_line(
        f"globus group get-by-subscription {meta['subscription_id']} -Fjson",
    )
