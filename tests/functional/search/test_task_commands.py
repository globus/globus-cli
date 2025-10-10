from globus_sdk.testing import load_response_set


def test_task_show(run_line):
    meta = load_response_set("cli.search").metadata
    task_id = meta["task_id"]

    result = run_line(["globus", "search", "task", "show", task_id])
    assert "SUCCESS (Task succeeded)" in result.output


def test_task_list(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    success_task_id = meta["task_id"]
    pending_task_id = meta["pending_task_id"]

    result = run_line(["globus", "search", "task", "list", index_id])

    found_success, found_pending = False, False
    for line in result.output.split("\n"):
        if success_task_id in line:
            found_success = True
            assert "SUCCESS" in line
        elif pending_task_id in line:
            found_pending = True
            assert "PENDING" in line
    assert found_success
    assert found_pending
