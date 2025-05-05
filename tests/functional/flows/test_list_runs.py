import uuid

import pytest

from globus_cli.commands.flows.run.list import ROLE_TYPES
from globus_sdk._testing import load_response


def test_list_runs_simple(run_line):
    meta = load_response("flows.list_runs").metadata
    first_run_id = meta["first_run_id"]

    result = run_line(["globus", "flows", "run", "list"])
    output_lines = result.output.split("\n")
    assert len(output_lines) >= 4

    header_line = output_lines[0]
    header_row = [item.strip() for item in header_line.split(" | ")]
    assert header_row == ["Run ID", "Flow Title", "Run Label", "Status"]

    first_line = output_lines[2]
    first_row = first_line.split(" | ")
    assert first_row[0] == first_run_id


def test_list_runs_filter_by_flow_id(run_line):
    meta = load_response("flows.list_runs", case="filter_flow_id").metadata
    flow_ids_to_use = meta["by_flow_id"].keys()

    # first test on each flow_id individually
    for flow_id in flow_ids_to_use:
        expect_num_results = meta["by_flow_id"][flow_id]["num"]
        result = run_line(
            ["globus", "flows", "run", "list", "--filter-flow-id", flow_id]
        )
        output_lines = result.output.split("\n")

        # allow for two header rows + final newline
        assert len(output_lines) == expect_num_results + 3

    # then combine them all into one filter and test again
    combined_filter_args = []
    for flow_id in flow_ids_to_use:
        combined_filter_args.extend(["--filter-flow-id", flow_id])
    result = run_line(["globus", "flows", "run", "list", *combined_filter_args])
    output_lines = result.output.split("\n")

    header_line = output_lines[0]
    header_row = [item.strip() for item in header_line.split(" | ")]
    assert header_row == ["Run ID", "Flow Title", "Run Label", "Status"]

    # trim header and final newline, compare against all of the filtered results
    lines = output_lines[2:-1]
    assert len(lines) == sum(data["num"] for data in meta["by_flow_id"].values())


@pytest.mark.parametrize("limit_delta", [-5, 0, 5])
def test_list_runs_paginated_response(run_line, limit_delta):
    meta = load_response("flows.list_runs", case="paginated").metadata

    # limit results to a number with a potential delta from the number of items
    # this helps exercise the CLI's limiting behavior
    limit = meta["total_items"] + limit_delta
    result = run_line(["globus", "flows", "run", "list", "--limit", str(limit)])
    output_lines = result.output.split("\n")
    # two header lines + final newline
    assert len(output_lines) == min(limit, meta["total_items"]) + 3

    header_line = output_lines[0]
    header_row = [item.strip() for item in header_line.split(" | ")]
    assert header_row == ["Run ID", "Flow Title", "Run Label", "Status"]

    for line in output_lines[2:-1]:
        row = line.split(" | ")
        try:
            uuid.UUID(row[0])
        except ValueError:
            pytest.fail(f"Run ID is not a valid UUID: {row[0]}")


def test_list_runs_filter_role(run_line):
    meta = load_response("flows.list_runs").metadata
    first_run_id = meta["first_run_id"]

    result = run_line(
        [
            "globus",
            "flows",
            "run",
            "list",
            "--filter-role",
            "run_owner",
            "--filter-role",
            "flow_run_manager",
        ]
    )

    expected = (
        "Run ID                               | Flow Title   | Run Label   | Status   \n"  # noqa: E501
        "------------------------------------ | ------------ | ----------- | ---------\n"  # noqa: E501
        f"{first_run_id} | My Cool Flow | My Cool Run | SUCCEEDED\n"  # noqa: E501
    )
    assert result.output == expected


def test_list_runs_invalid_filter_role(run_line):
    load_response("flows.list_runs")

    invalid_filter_role = "up-up-down-down-left-right-left-right-b-a"
    role_types = ", ".join(f"'{role}'" for role in ROLE_TYPES)
    expected_error = (
        f"Error: Invalid value for '--filter-role': '{invalid_filter_role}' "
        f"is not one of {role_types}."
    )

    result = run_line(
        f"globus flows run list --filter-role {invalid_filter_role}",
        assert_exit_code=2,
    )
    assert expected_error in result.stderr
