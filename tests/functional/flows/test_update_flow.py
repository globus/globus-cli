import json
import re
import uuid
from itertools import chain

import pytest
from globus_sdk._testing import RegisteredResponse, get_last_request, load_response

from tests.functional.flows.test_create_flow import (
    SPECIAL_PRINCIPALS,
    IdentityPool,
    value_for_field_from_output,
)


def test_update_flow_text_output(run_line):
    # Load the response mock and extract metadata
    response = load_response("flows.update_flow")
    flow_id = response.metadata["flow_id"]
    definition = response.json["definition"]
    input_schema = response.json["input_schema"]
    keywords = response.json["keywords"]
    title = response.json["title"]
    subtitle = response.json["subtitle"]
    description = response.json["description"]
    flow_owner = response.json["flow_owner"]
    flow_administrators = response.json["flow_administrators"]
    flow_starters = response.json["flow_starters"]
    flow_viewers = response.json["flow_viewers"]

    pool = IdentityPool()

    # Configure the identities for all roles
    pool.assign("owner", [flow_owner])
    pool.assign("administrators", flow_administrators)
    pool.assign("starters", flow_starters)
    pool.assign("viewers", flow_viewers)

    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": list(pool.identities.values()),
            },
        )
    )

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
        "Created At",
        "Updated At",
        "Administrators",
        "Starters",
        "Viewers",
    }
    actual_fields = set(re.findall(r"^[\w ]+(?=:)", result.output, flags=re.M))
    assert expected_fields == actual_fields, "Expected and actual field sets differ"

    # Check values for simple fields
    simple_fields = {
        "Owner": pool.get_assigned_usernames("owner")[0],
        "Title": title or "",
        "Subtitle": subtitle or "",
        "Description": description or "",
    }

    for name, value in simple_fields.items():
        assert value_for_field_from_output(name, result.output) == value

    # Check all multi-value fields
    expected_sets = {
        "Keywords": set(keywords),
        "Administrators": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_administrators
            ],
            *pool.get_assigned_usernames("administrators"),
        },
        "Starters": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_starters
            ],
            *pool.get_assigned_usernames("starters"),
        },
        "Viewers": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_viewers
            ],
            *pool.get_assigned_usernames("viewers"),
        },
    }

    for name, expected_values in expected_sets.items():
        match_list = set(value_for_field_from_output(name, result.output).split(","))
        assert match_list == expected_values


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
    omitted_keys = {"flow_administrators", "flow_starters", "flow_viewers", "keywords"}
    assert json.loads(request.body).keys() & omitted_keys == set()


@pytest.mark.parametrize("option", ["definition", "input-schema"])
def test_json_object_option_validation(option, run_line):
    """Ensure options that must be JSON objects are validated as such."""

    command = f"globus flows update {uuid.uuid4()} --{option} '[]'"
    result = run_line(command, assert_exit_code=2)
    assert "must be a JSON object" in result.stderr
