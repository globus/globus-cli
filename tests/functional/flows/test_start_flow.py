from __future__ import annotations

import json
import re
import uuid

import pytest
import responses
from globus_sdk.testing import RegisteredResponse, load_response


def test_start_flow_text_output(run_line, add_flow_login, load_identities_for_flow_run):
    # Load the response mock and extract critical metadata.
    loaded_response = load_response("flows.run_flow")
    response, meta = loaded_response.json, loaded_response.metadata

    flow_id = meta["flow_id"]
    body = meta["request_params"]["body"]
    tags = meta["request_params"]["tags"]
    label = meta["request_params"]["label"]
    run_monitors = meta["request_params"]["run_monitors"]
    run_managers = meta["request_params"]["run_managers"]
    add_flow_login(flow_id)

    pool = load_identities_for_flow_run(response)

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
        "Flow Title",
        "Run ID",
        "Run Label",
        "Run Owner",
        "Run Managers",
        "Run Monitors",
        "Run Tags",
        "Started At",
        "Completed At",
        "Status",
    }
    actual_fields = set(re.findall(r"^[\w ]+(?=:)", result.output, flags=re.M))
    assert expected_fields == actual_fields, "Expected and actual field sets differ"

    assert _get_output_value("Run Tags", result.output) == ", ".join(response["tags"])

    assert_usernames(result, pool, "Run Owner", [response["run_owner"]])
    assert_usernames(result, pool, "Run Managers", response["run_managers"])
    assert_usernames(result, pool, "Run Monitors", response["run_monitors"])


def assert_usernames(result, pool, field_name, principals):
    expected_usernames = {pool.get_username(principal) for principal in principals}

    output_value = _get_output_value(field_name, result.output)
    output_usernames = [x.strip() for x in output_value.split(",")]
    assert expected_usernames == set(output_usernames)


def _get_output_value(name, output):
    """
    Return the value for a specified field from the output of a command.
    """
    match = re.search(rf"^{name}:[^\S\n\r]+(?P<value>.*)$", output, flags=re.M)
    assert match is not None
    return match.group("value")


def test_start_flow_prompts_session_reconsent_on_gare(run_line, add_flow_login):
    """
    When an HA flow is started but a session requirement is not met, ensure we properly
    instruct the user to update their session based on the supplied GARE.
    """
    flow_id = str(uuid.uuid4())
    required_policy_id = str(uuid.uuid4())

    add_flow_login(flow_id)

    RegisteredResponse(
        service="flows",
        path=f"/flows/{flow_id}/run",
        method="POST",
        status=403,
        json={
            "code": "AuthenticationPolicyRequired",
            "authorization_parameters": {
                "session_message": (
                    "Globus Flows detected an unsatisfied session policy for this "
                    "resource."
                ),
                "session_required_policies": [required_policy_id],
            },
            "error": {
                "code": "AUTHENTICATION_POLICY_REQUIRED",
                "detail": (
                    "You do not have the necessary permissions to perform this action "
                    "on the flow with id value 50d4ecb4-206b-4669-8c99-c18b05f30e7d. "
                    "Missing permissions: RUN."
                ),
            },
            "debug_id": "34a8a8ad-580f-4c44-a411-7e0fa05df370",
        },
    ).add()

    result = run_line(f"globus flows start {flow_id} --input {{}}", assert_exit_code=4)

    assert f"globus session update --policy '{required_policy_id}'" in result.stdout


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
    run_line,
    add_flow_login,
    load_identities_for_flow_run,
    activity_arg,
    expect_sent_policy,
):
    response = load_response("flows.run_flow")
    flow_id = response.metadata["flow_id"]
    add_flow_login(flow_id)

    load_identities_for_flow_run(response.json)

    add_args = []
    if activity_arg is not None:
        add_args = ["--activity-notification-policy", activity_arg]

    run_line(["globus", "flows", "start", flow_id] + add_args)

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
