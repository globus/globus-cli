from __future__ import annotations

import json
import urllib.parse

from globus_sdk.testing import get_last_request, load_response


def test_list_web_inputs(run_line):
    meta = load_response("flows.list_web_inputs").metadata

    result = run_line("globus flows web-input list")

    output_lines = result.output.rstrip("\n").split("\n")
    header = output_lines[0]
    for column in (
        "Web Input ID",
        "Status",
        "Input Type",
        "Title",
        "Flow Title",
        "Run Label",
    ):
        assert column in header

    row = output_lines[2].split(" | ")
    assert row[0] == meta["first_web_input_id"]

    # confirm the default orderby was sent, and no filters
    last_req = get_last_request()
    parsed_params = urllib.parse.parse_qs(urllib.parse.urlparse(last_req.url).query)
    assert parsed_params["orderby"] == ["created_timestamp DESC"]
    assert "filter_roles" not in parsed_params
    assert "filter_states" not in parsed_params


def test_list_web_inputs_json(run_line):
    load_response("flows.list_web_inputs")

    result = run_line("globus flows web-input list -F json")
    output = json.loads(result.output)
    assert "web_input_summaries" in output


def test_list_web_inputs_filter_role_and_state(run_line):
    load_response("flows.list_web_inputs")

    result = run_line(
        [
            "globus",
            "flows",
            "web-input",
            "list",
            "--filter-role",
            "respondent",
            "--filter-state",
            "open",
        ]
    )
    assert result.exit_code == 0

    last_req = get_last_request()
    parsed_params = urllib.parse.parse_qs(urllib.parse.urlparse(last_req.url).query)
    assert parsed_params["filter_roles"] == ["respondent"]
    assert parsed_params["filter_states"] == ["open"]


def test_list_web_inputs_invalid_filter_role(run_line):
    load_response("flows.list_web_inputs")

    run_line(
        [
            "globus",
            "flows",
            "web-input",
            "list",
            "--filter-role",
            "this-certainly-isnt-a-valid-role",
        ],
        assert_exit_code=2,
    )


def test_list_web_inputs_paginated_response(run_line):
    meta = load_response("flows.list_web_inputs", case="paginated").metadata
    total_items = meta["total_items"]

    result = run_line("globus flows web-input list --limit 1000")
    output_lines = result.output.split("\n")[:-1]  # trim the final newline/empty str
    # 2 header lines + total_items data lines
    assert len(output_lines) == total_items + 2


def test_list_web_inputs_empty_list(run_line):
    load_response("flows.list_web_inputs", case="empty")

    result = run_line("globus flows web-input list")
    output_lines = result.output.rstrip("\n").split("\n")
    assert len(output_lines) == 2
