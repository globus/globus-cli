from globus_sdk.testing import load_response_set


def test_task_event_list_success(run_line):
    meta = load_response_set("cli.task_event_list").metadata
    task_id = meta["task_id"]
    result = run_line(f"globus task event-list {task_id}")
    assert "Canceled by the task owner" in result.output
