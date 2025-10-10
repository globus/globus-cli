import datetime
import json

import pytest
from globus_sdk.testing import (
    RegisteredResponse,
    load_response,
    load_response_set,
    register_response_set,
)
from globus_sdk.testing.data.flows.get_run_logs import (
    PAGINATED_RUN_LOG_RESPONSES,
    RUN_ID,
)
from responses.matchers import query_param_matcher

EXPECTED_EVENT_CODES = [
    "FlowStarted",
    "FlowSucceeded",
    "PassStarted",
    "PassCompleted",
    "ActionStarted",
    "ActionCompleted",
]


# a minimal stub response meant to match the specific usage in
# 'globus flows run show-logs'
def _setup_get_response(run_id, *, status="ACTIVE"):
    load_response(
        RegisteredResponse(
            service="flows",
            method="GET",
            path=f"/runs/{run_id}",
            json={"status": status},
        )
    )


def test_run_show_logs_table(run_line):
    meta = load_response("flows.get_run_logs").metadata
    run_id = meta["run_id"]
    _setup_get_response(run_id)

    result = run_line(["globus", "flows", "run", "show-logs", run_id])
    output_lines = result.output.splitlines()
    assert len(output_lines) == 6  # 4 events + 2 header

    header_line = output_lines[0]
    header_items = [item.strip() for item in header_line.split("|")]
    assert header_items == ["Time", "Code", "Description"]

    first_line = output_lines[2]
    first_row = [item.strip() for item in first_line.split("|")]
    assert first_row == [
        "2023-04-25T18:54:30.683000+00:00",
        "FlowStarted",
        "The Flow Instance started execution",
    ]


@pytest.mark.parametrize("run_inactive", (True, False))
def test_run_show_logs_shows_hints(run_line, monkeypatch, run_inactive):
    # force interactive and patch detection methods to get command hints to print
    monkeypatch.setenv("GLOBUS_CLI_INTERACTIVE", "1")
    monkeypatch.setattr("globus_cli.termio.err_is_terminal", lambda: True)
    monkeypatch.setattr("globus_cli.termio.out_is_terminal", lambda: True)

    meta = load_response("flows.get_run_logs").metadata
    run_id = meta["run_id"]
    _setup_get_response(run_id, status="INACTIVE" if run_inactive else "ACTIVE")

    hint_regexes = [r"Displaying summary data\."]
    if run_inactive:
        hint_regexes.append(r"NOTE: This run is INACTIVE\.")
    run_line(
        ["globus", "flows", "run", "show-logs", run_id], search_stderr=hint_regexes
    )


def test_run_show_logs_text_records(run_line):
    meta = load_response("flows.get_run_logs").metadata
    run_id = meta["run_id"]
    _setup_get_response(run_id)

    result = run_line(["globus", "flows", "run", "show-logs", run_id, "--details"])
    output_sections = [item.splitlines() for item in result.output.split("\n\n")]
    assert len(output_sections) == 4  # 4 events

    for section in output_sections:
        assert len(section) == 4
        field_map = {
            k: v.strip() for k, v in [line.split(":", maxsplit=1) for line in section]
        }
        assert isinstance(
            datetime.datetime.fromisoformat(field_map["Time"]), datetime.datetime
        )
        assert field_map["Code"] in EXPECTED_EVENT_CODES
        assert isinstance(field_map["Description"], str)
        assert isinstance(json.loads(field_map["Details"]), dict)


@pytest.mark.parametrize("limit", [3, 10, 12])
def test_run_show_logs_paginated_response(run_line, limit):
    register_response_set(
        "get_run_logs_paginated",
        {
            "page0": {
                "service": "flows",
                "method": "GET",
                "path": f"/runs/{RUN_ID}/log",
                "json": PAGINATED_RUN_LOG_RESPONSES[0],
                "match": [query_param_matcher(params={"reverse_order": "False"})],
            },
            "page1": {
                "service": "flows",
                "method": "GET",
                "path": f"/runs/{RUN_ID}/log",
                "json": PAGINATED_RUN_LOG_RESPONSES[1],
                "match": [
                    query_param_matcher(
                        params={
                            "reverse_order": "False",
                            "marker": PAGINATED_RUN_LOG_RESPONSES[0]["marker"],
                        },
                    )
                ],
            },
        },
    )
    load_response_set("get_run_logs_paginated")
    run_id = RUN_ID
    _setup_get_response(run_id)

    result = run_line(
        ["globus", "flows", "run", "show-logs", run_id, "--limit", str(limit)]
    )
    output_lines = result.output.splitlines()

    assert len(output_lines) == limit + 2  # num events + 2 header

    header_line = output_lines[0]
    header_items = [item.strip() for item in header_line.split("|")]
    assert header_items == ["Time", "Code", "Description"]

    for line in output_lines[2:]:
        time, code, _ = (value.strip() for value in line.split("|"))
        assert isinstance(datetime.datetime.fromisoformat(time), datetime.datetime)
        assert code in EXPECTED_EVENT_CODES
