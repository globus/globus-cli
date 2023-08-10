import datetime
import json

from globus_sdk._testing import load_response


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
        assert field_map["Code"] in [
            "FlowStarted",
            "FlowSucceeded",
            "ActionStarted",
            "ActionCompleted",
        ]
        assert isinstance(field_map["Description"], str)
        assert isinstance(json.loads(field_map["Details"]), dict)
