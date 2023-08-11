import datetime
import json

import pytest
from globus_sdk._testing import load_response, load_response_set, register_response_set
from globus_sdk._testing.data.flows.get_run_logs import (
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


def test_run_show_logs_table(run_line):
    meta = load_response("flows.get_run_logs").metadata
    run_id = meta["run_id"]

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


def test_run_show_logs_text_records(run_line):
    meta = load_response("flows.get_run_logs").metadata
    run_id = meta["run_id"]

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
            "page0": dict(
                service="flows",
                method="GET",
                path=f"/runs/{RUN_ID}/log",
                json=PAGINATED_RUN_LOG_RESPONSES[0],
                match=[query_param_matcher(params={"reverse_order": "False"})],
            ),
            "page1": dict(
                service="flows",
                method="GET",
                path=f"/runs/{RUN_ID}/log",
                json=PAGINATED_RUN_LOG_RESPONSES[1],
                match=[
                    query_param_matcher(
                        params={
                            "reverse_order": "False",
                            "marker": PAGINATED_RUN_LOG_RESPONSES[0]["marker"],
                        },
                    )
                ],
            ),
        },
    )
    load_response_set("get_run_logs_paginated")
    run_id = RUN_ID

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
