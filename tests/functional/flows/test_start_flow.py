from __future__ import annotations

import json
import re
import typing as t

import pytest
import responses
from globus_sdk.testing import load_response


def test_start_flow_text_output(run_line, add_flow_login, get_identities_mocker):
    # Load the response mock and extract critical metadata.
    response = load_response("flows.run_flow")
    flow_id = response.metadata["flow_id"]
    body = response.metadata["request_params"]["body"]
    tags = response.metadata["request_params"]["tags"]
    label = response.metadata["request_params"]["label"]
    run_monitors = response.metadata["request_params"]["run_monitors"]
    run_managers = response.metadata["request_params"]["run_managers"]
    add_flow_login(flow_id)

    identity_info = _setup_identity_mock_response(
        get_identities_mocker, response.json["run_owner"], run_managers, run_monitors
    )

    # Construct the command line.
    arguments = [f"'{flow_id}'", "--input", f"'{json.dumps(body)}'"]
    for run_manager in run_managers:
        arguments.extend(("--manager", f"'{run_manager}'"))
    for run_monitor in run_monitors:
        arguments.extend(("--monitor", f"'{run_monitor}'"))
    for tag in tags:
        arguments.extend(("--tag", f"'{tag}'"))
    if label is not None:
        arguments.extend(("--label", f"'{label}'"))

    result = run_line(f"globus flows start {' '.join(arguments)}")

    # all fields present
    expected_fields = {
        "Flow ID",
        "Flow title",
        "Run ID",
        "Run label",
        "Run owner",
        "Run managers",
        "Run monitors",
        "Run tags",
    }
    actual_fields = set(re.findall(r"^[\w ]+(?=:)", result.output, flags=re.M))
    assert expected_fields == actual_fields, "Expected and actual field sets differ"

    tag_match = re.search(r"^Run tags:\s+(?P<tags>.+)$", result.output, flags=re.M)
    assert tag_match is not None
    assert ", ".join(tags) in tag_match.group("tags")

    owner_match = re.search(r"^Run owner:\s+(?P<owner>.+)$", result.output, flags=re.M)
    assert owner_match is not None
    assert owner_match.group("owner") == identity_info["owner"]["username"]

    managers_match = re.search(
        r"^Run managers:\s+(?P<managers>.+)$", result.output, flags=re.M
    )
    assert managers_match is not None
    assert managers_match.group("managers") == ", ".join(
        identity["username"] for identity in identity_info["run_managers"]
    )

    monitors_match = re.search(
        r"^Run monitors:\s+(?P<monitors>.+)$", result.output, flags=re.M
    )
    assert monitors_match is not None
    assert monitors_match.group("monitors") == ", ".join(
        identity["username"] for identity in identity_info["run_monitors"]
    )


def test_start_flow_rejects_non_object_input(run_line, add_flow_login):
    # setup test requirements for success to ensure that the test won't be sensitive to
    # the order in which checks which happen
    # (e.g. login check happening before the input shape check)
    response = load_response("flows.run_flow")
    flow_id = response.metadata["flow_id"]
    add_flow_login(flow_id)

    result = run_line(
        ["globus", "flows", "start", flow_id, "--input", json.dumps(["foo", "bar"])],
        assert_exit_code=2,
    )
    assert "Flow input must be a JSON object" in result.stderr


@pytest.mark.parametrize(
    "activity_arg, expect_sent_policy",
    (
        (None, None),
        ("FAILED", {"status": ["FAILED"]}),
        ("INACTIVE,SUCCEEDED,FAILED", {"status": ["INACTIVE", "SUCCEEDED", "FAILED"]}),
        ('{"status": ["INACTIVE", "FAILED"]}', {"status": ["INACTIVE", "FAILED"]}),
        ("succeeded,", {"status": ["SUCCEEDED"]}),
    ),
)
def test_start_flow_sends_expected_activity_notification_policy(
    run_line, add_flow_login, get_identities_mocker, activity_arg, expect_sent_policy
):
    response = load_response("flows.run_flow")
    flow_id = response.metadata["flow_id"]
    add_flow_login(flow_id)

    _setup_identity_mock_response(
        get_identities_mocker,
        response.json["run_owner"],
        response.metadata["request_params"]["run_managers"],
        response.metadata["request_params"]["run_monitors"],
    )

    add_args = []
    if activity_arg is not None:
        add_args = ["--activity-notification-policy", activity_arg]

    run_line(
        [
            "globus",
            "flows",
            "start",
            flow_id,
        ]
        + add_args
    )

    flows_requests = [
        call.request
        for call in responses.calls
        if call.request.url.startswith("https://flows.automate.globus.org")
    ]
    assert len(flows_requests) == 1
    start_req = flows_requests[0]
    sent_body = json.loads(start_req.body)

    if expect_sent_policy is not None:
        assert "activity_notification_policy" in sent_body
        assert sent_body["activity_notification_policy"] == expect_sent_policy
    else:
        assert "activity_notification_policy" not in sent_body


def _setup_identity_mock_response(
    get_identities_mocker,
    run_owner: str,
    run_managers: list[str],
    run_monitors: list[str],
) -> dict[str, t.Any]:
    # Configure identities.
    owner_identity = {
        "username": "yogi@jellystone.park",
        "name": "Yogi",
        "id": run_owner.split(":")[-1],
    }
    run_manager_identities = [
        {
            "username": "booboo@jellystone.park",
            "name": "Boo Boo",
            "id": run_managers[0].split(":")[-1],
        },
    ]
    run_monitor_identities = [
        {
            "username": "snaggle@jellystone.park",
            "name": "Snagglepuss",
            "id": run_monitors[0].split(":")[-1],
        },
        {
            "username": "yakky@jellystone.park",
            "name": "Yakky Doodle",
            "id": run_monitors[1].split(":")[-1],
        },
    ]
    get_identities_mocker.configure(
        [owner_identity, *run_manager_identities, *run_monitor_identities]
    )

    return {
        "owner": owner_identity,
        "run_managers": run_manager_identities,
        "run_monitors": run_monitor_identities,
    }
