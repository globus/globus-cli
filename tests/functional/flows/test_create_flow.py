import json
import re
import uuid

import pytest
import responses
from globus_sdk.testing import load_response


def test_create_flow_text_output(run_line, load_identities_for_flow):
    # Load the response mock and extract metadata
    loaded_response = load_response("flows.create_flow")
    response, meta = loaded_response.json, loaded_response.metadata

    definition = meta["params"]["definition"]
    input_schema = meta["params"]["input_schema"]
    keywords = meta["params"]["keywords"]
    title = meta["params"]["title"]
    subtitle = meta["params"]["subtitle"]
    description = meta["params"]["description"]
    flow_administrators = meta["params"]["flow_administrators"]
    flow_starters = meta["params"]["flow_starters"]
    flow_viewers = meta["params"]["flow_viewers"]
    flow_run_managers = meta["params"]["run_managers"]
    flow_run_monitors = meta["params"]["run_monitors"]

    pool = load_identities_for_flow(response)

    # Construct the command line
    command = ["globus", "flows", "create", title, json.dumps(definition)]
    for flow_administrator in flow_administrators:
        command.extend(("--administrator", flow_administrator))
    for flow_starter in flow_starters:
        command.extend(("--starter", flow_starter))
    for flow_viewer in flow_viewers:
        command.extend(("--viewer", flow_viewer))
    for flow_run_manager in flow_run_managers:
        command.extend(("--run-manager", flow_run_manager))
    for flow_run_monitor in flow_run_monitors:
        command.extend(("--run-monitor", flow_run_monitor))
    for keyword in keywords:
        command.extend(("--keyword", keyword))
    if input_schema is not None:
        command.extend(("--input-schema", json.dumps(input_schema)))
    if subtitle is not None:
        command.extend(("--subtitle", subtitle))
    if description is not None:
        command.extend(("--description", description))

    result = run_line(command)

    # Check all fields are present
    expected_fields = {
        "Flow ID",
        "Title",
        "Subtitle",
        "Description",
        "Keywords",
        "Owner",
        "Subscription ID",
        "Created At",
        "Updated At",
        "Administrators",
        "Starters",
        "Viewers",
        "Run Managers",
        "Run Monitors",
    }

    actual_fields = set(re.findall(r"^[\w ]+(?=:)", result.output, flags=re.M))
    assert expected_fields == actual_fields, "Expected and actual field sets differ"

    assert _get_output_value("Title", result.output) == title or ""
    assert _get_output_value("Subtitle", result.output) == subtitle or ""
    assert _get_output_value("Description", result.output) == description or ""
    assert _get_output_value("Keywords", result.output) == ", ".join(keywords)

    assert_usernames(result, pool, "Owner", [response["flow_owner"]])
    assert_usernames(result, pool, "Administrators", response["flow_administrators"])
    assert_usernames(result, pool, "Starters", response["flow_starters"])
    assert_usernames(result, pool, "Viewers", response["flow_viewers"])
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


@pytest.mark.parametrize(
    "subscription_id, valid",
    (
        ("dummy-invalid-subscription-id", False),
        (str(uuid.UUID(int=1)), True),
    ),
)
def test_create_flow_with_subscription_id(
    run_line, load_identities_for_flow, subscription_id, valid
):
    # Load the response mock and extract metadata
    response = load_response("flows.create_flow")
    response_data = response.json

    definition = response.metadata["params"]["definition"]
    input_schema = response.metadata["params"]["input_schema"]
    keywords = response.metadata["params"]["keywords"]
    title = response.metadata["params"]["title"]
    subtitle = response.metadata["params"]["subtitle"]
    description = response.metadata["params"]["description"]

    flow_administrators = response.metadata["params"]["flow_administrators"]
    flow_starters = response.metadata["params"]["flow_starters"]
    flow_viewers = response.metadata["params"]["flow_viewers"]
    run_managers = response.metadata["params"]["run_managers"]
    run_monitors = response.metadata["params"]["run_monitors"]

    load_identities_for_flow(response_data)

    # Construct the command line
    command = [
        "globus",
        "flows",
        "create",
        title,
        json.dumps(definition),
        "--subscription-id",
        subscription_id,
    ]
    for flow_administrator in flow_administrators:
        command.extend(("--administrator", flow_administrator))
    for flow_starter in flow_starters:
        command.extend(("--starter", flow_starter))
    for flow_viewer in flow_viewers:
        command.extend(("--viewer", flow_viewer))
    for keyword in keywords:
        command.extend(("--keyword", keyword))
    if input_schema is not None:
        command.extend(("--input-schema", json.dumps(input_schema)))
    if subtitle is not None:
        command.extend(("--subtitle", subtitle))
    if description is not None:
        command.extend(("--description", description))
    if run_managers is not None:
        for run_manager in run_managers:
            command.extend(("--run-manager", run_manager))
    if run_monitors is not None:
        for run_monitor in run_monitors:
            command.extend(("--run-monitor", run_monitor))

    run_line(command, assert_exit_code=0 if valid else 2)
    if valid:
        request = next(
            call
            for call in responses.calls
            if "flows.automate.globus.org" in call.request.url
        ).request
        assert json.loads(request.body)["subscription_id"] == subscription_id
