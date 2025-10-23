import json
import re
import uuid
from itertools import chain

import pytest
from globus_sdk.testing import get_last_request, load_response


def test_update_flow_text_output(run_line, load_identities_for_flow):
    # Load the response mock and extract metadata
    loaded_response = load_response("flows.update_flow")
    response, meta = loaded_response.json, loaded_response.metadata

    flow_id = meta["flow_id"]
    definition = response["definition"]
    input_schema = response["input_schema"]
    keywords = response["keywords"]
    title = response["title"]
    subtitle = response["subtitle"]
    description = response["description"]
    flow_owner = response["flow_owner"]
    flow_administrators = response["flow_administrators"]
    flow_starters = response["flow_starters"]
    flow_viewers = response["flow_viewers"]
    run_managers = response["run_managers"]
    run_monitors = response["run_monitors"]

    pool = load_identities_for_flow(response)

    # Construct the command line
    options = [
        ("--definition", json.dumps(definition)),
        ("--input-schema", json.dumps(input_schema)),
        ("--title", title),
        ("--subtitle", subtitle),
        ("--description", description),
        ("--owner", flow_owner),
        ("--administrators", ",".join(flow_administrators)),
        ("--starters", ",".join(flow_starters)),
        ("--viewers", ",".join(flow_viewers)),
        ("--keywords", ",".join(keywords)),
        ("--subscription-id", str(uuid.uuid4())),
        ("--run-managers", ",".join(run_managers)),
        ("--run-monitors", ",".join(run_monitors)),
    ]

    command = ["globus", "flows", "update", flow_id, *chain.from_iterable(options)]

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
        "High Assurance",
        "Authentication Policy ID",
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


@pytest.mark.parametrize("name", ("administrators", "starters", "viewers", "keywords"))
def test_empty_strings_for_csv_options(name, run_line):
    """Verify that empty strings are converted to empty lists in the request body."""

    flow_id = load_response("flows.update_flow").metadata["flow_id"]
    # "--format json" prevents Auth calls that would need to be mocked.
    command = f'globus flows update {flow_id} --{name} "" --format json'
    run_line(command)

    request = get_last_request()
    key = name if name == "keywords" else f"flow_{name}"
    assert json.loads(request.body)[key] == []


def test_omitted_options(run_line):
    """Verify that omitted CSV options are not included in the request body."""

    flow_id = load_response("flows.update_flow").metadata["flow_id"]

    # "--format json" prevents Auth calls that would need to be mocked.
    command = f"globus flows update {flow_id} --format json"
    run_line(command)

    request = get_last_request()
    omitted_keys = {
        "flow_administrators",
        "flow_starters",
        "flow_viewers",
        "keywords",
        "subscription_id",
    }
    assert json.loads(request.body).keys() & omitted_keys == set()


@pytest.mark.parametrize("option", ["definition", "input-schema"])
def test_json_object_option_validation(option, run_line):
    """Ensure options that must be JSON objects are validated as such."""

    command = f"globus flows update {uuid.uuid4()} --{option} '[]'"
    result = run_line(command, assert_exit_code=2)
    assert "must be a JSON object" in result.stderr
