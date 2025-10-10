import json
import re
import uuid
from itertools import chain

import pytest
from globus_sdk.testing import (
    get_last_request,
    load_response_set,
    register_response_set,
)


@pytest.fixture(scope="session", autouse=True)
def _register_responses():
    # Missing (defensive case for beta API)
    register_response_set(
        "cli.flow_validate.missing",
        {
            "default": {
                "service": "flows",
                "path": "/flows/validate",
                "method": "POST",
                "json": {},
            },
        },
    )
    # Empty scopes
    register_response_set(
        "cli.flow_validate.none",
        {
            "default": {
                "service": "flows",
                "path": "/flows/validate",
                "method": "POST",
                "json": {"scopes": {}, "analysis": {"number_of_possibilities": 0}},
            },
        },
        metadata={"possibility_count": None},
    )
    # User scopes
    register_response_set(
        "cli.flow_validate.user",
        {
            "default": {
                "service": "flows",
                "path": "/flows/validate",
                "method": "POST",
                "json": {
                    "scopes": {
                        "User": ["urn:globus:auth:scope:transfer.api.globus.org:all"]
                    },
                    "analysis": {"number_of_possibilities": 1},
                },
            },
        },
        metadata={"possibility_count": 1},
    )
    # Multiple Flow and User scopes
    register_response_set(
        "cli.flow_validate.multi",
        {
            "default": {
                "service": "flows",
                "path": "/flows/validate",
                "method": "POST",
                "json": {
                    "scopes": {
                        "User": ["urn:globus:auth:scope:foo.api.globus.org:all"],
                        "Flow": [
                            "urn:globus:auth:scope:bar.api.globus.org:all",
                            "urn:globus:auth:scope:baz.api.globus.org:all",
                        ],
                    },
                    "analysis": {"number_of_possibilities": 1000000},
                },
            },
        },
        metadata={"possibility_count": 1000000},
    )
    # Scope resolution error
    ap_url = "https://domain.example/bad"
    register_response_set(
        "cli.flow_validate.scope_resolution_failed",
        {
            "default": {
                "service": "flows",
                "path": "/flows/validate",
                "method": "POST",
                "status": 409,
                "json": {
                    "error": {
                        "code": "SCOPE_RESOLUTION_FAILED",
                        "detail": (
                            "Failed to resolve scope for Action Provider "
                            f"at '{ap_url}': upstream did not respond"
                        ),
                    },
                    "debug_id": str(uuid.uuid4()),
                },
            }
        },
        metadata={"ap_url": ap_url},
    )


@pytest.mark.parametrize(
    "response_set, expected_table_data",
    [
        pytest.param("cli.flow_validate.none", [], id="no_scopes"),
        pytest.param(
            "cli.flow_validate.user",
            [["User", "urn:globus:auth:scope:transfer.api.globus.org:all"]],
            id="user_scopes",
        ),
        pytest.param(
            "cli.flow_validate.multi",
            [
                ["User", "urn:globus:auth:scope:foo.api.globus.org:all"],
                ["Flow", "urn:globus:auth:scope:bar.api.globus.org:all"],
                ["Flow", "urn:globus:auth:scope:baz.api.globus.org:all"],
            ],
            id="multi_scopes",
        ),
    ],
)
def test_validate_flow_scope_output(response_set, expected_table_data, run_line):
    # Load the response mock and extract metadata
    load_response_set(response_set)
    definition = {"StartAt": "a", "States": {"a": {"Type": "Pass", "End": True}}}

    # Construct the command line
    command = ["globus", "flows", "validate", json.dumps(definition)]

    result = run_line(command)

    if not expected_table_data:
        # Check for the "No scopes discovered" message
        assert "No scopes discovered" in result.output
    else:
        # Get the rows of the table
        headers, table_data = _parse_table_content(result.output)[0]
        # Check all fields are present
        assert headers == ["RunAs", "Scope"]
        # Check the entries
        assert len(table_data) == len(expected_table_data)
        assert len(table_data[0]) == 2
        assert table_data == expected_table_data


def test_validate_flow_scope_output_missing(run_line):
    load_response_set("cli.flow_validate.missing")
    result = run_line(["globus", "flows", "validate", "{}"])
    assert "Discovered Scopes" not in result.output


@pytest.mark.parametrize("input_schema", [None, {}])
def test_validate_flow_input_schema(input_schema, run_line):
    load_response_set("cli.flow_validate.none")
    definition = {"StartAt": "a", "States": {"a": {"Type": "Pass", "End": True}}}

    # Construct the command line
    options = [(json.dumps(definition),)]
    if input_schema is not None:
        options.append(("--input-schema", json.dumps(input_schema)))

    command = ["globus", "flows", "validate", *chain.from_iterable(options)]
    result = run_line(command)

    assert "No scopes discovered" in result.output

    if input_schema is None:
        # We should not have sent the input schema in the request
        assert json.loads(get_last_request().body) == {"definition": definition}
    else:
        # We should have sent the input schema in the request
        assert json.loads(get_last_request().body) == {
            "definition": definition,
            "input_schema": input_schema,
        }


@pytest.mark.parametrize(
    "response_set",
    [
        pytest.param("cli.flow_validate.none", id="no_scopes"),
        pytest.param("cli.flow_validate.user", id="user_scopes"),
        pytest.param("cli.flow_validate.multi", id="multi_scopes"),
    ],
)
def test_validate_flow_analysis_output(response_set, run_line):
    # Load the response mock and extract metadata
    metadata = load_response_set(response_set).metadata
    expected_possibility_count = metadata.get("possibility_count")
    definition = {"StartAt": "a", "States": {"a": {"Type": "Pass", "End": True}}}

    # Construct the command line
    command = ["globus", "flows", "validate", json.dumps(definition)]
    result = run_line(command)

    if expected_possibility_count is not None:
        assert (
            f"Possible State Traversals: {expected_possibility_count}" in result.output
        )
    else:
        # Should be omitted entirely
        assert "Possible State Traversals" not in result.output


def test_validate_flow_analysis_output_missing(run_line):
    load_response_set("cli.flow_validate.missing")
    result = run_line(["globus", "flows", "validate", "{}"])
    assert "Analysis" not in result.output


def test_validate_flow_scope_resolution_failed(run_line):
    """Verify that KeyError is not raised when 'message' is missing."""

    load_response_set("cli.flow_validate.scope_resolution_failed")
    run_line(
        ["globus", "flows", "validate", "{}"],
        assert_exit_code=1,
        search_stderr="SCOPE_RESOLUTION_FAILED",
    )


def _parse_table_content(output):
    """
    Parse the output of a command, searching for tables in the output and returning
    a list of headers and a list of rows (which are lists of cell values).

    Expects a table with divider lines of the form `--- | --- | ---` and rows of the
    form `value | value | value`.

    Returns a list of tuples where each tuple represents a parsed table and is
    comprised of a list of headers and a list of rows.

    Raises a ValueError if no table is found in the output.
    """
    # Find the table divider
    lines = output.splitlines()
    divider_indices = [
        i for i, line in enumerate(lines) if re.fullmatch(r"-+ \| [-| ]*", line)
    ]

    if not divider_indices:
        raise ValueError("No table found in output")

    tables = []
    for divider_index in divider_indices:
        # Parse the headers and rows
        headers = [header.strip() for header in lines[divider_index - 1].split(" | ")]
        rows = lines[divider_index + 1 :]
        # Turn the rows into a table data as a list of lists
        table_data = []
        for row in rows:
            # Get the cells in the row
            cells = [cell.strip() for cell in row.split(" | ")]
            # Is this a valid row?
            if len(cells) != len(headers):
                break
            # Add the row to the table data
            table_data.append(cells)
        # Add the table to the list of tables
        tables.append((headers, table_data))

    return tables
