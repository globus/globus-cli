import json
import uuid

import pytest
from globus_sdk.testing import RegisteredResponse


def test_cancel_one(run_line):
    """Task cancellation works for a single task."""
    # TODO: swap out this response for an SDK-provided one once it's available
    # ref: https://github.com/globus/globus-sdk-python/pull/1354
    task_id = str(uuid.uuid4())
    RegisteredResponse(
        service="transfer",
        path=f"/v0.10/task/{task_id}/cancel",
        method="POST",
        json={
            "DATA_TYPE": "result",
            "code": "Canceled",
            "message": "The task has been cancelled successfully.",
            "resource": f"/task/{task_id}/cancel",
            "request_id": "ABCdef789",
        },
    ).add()

    result = run_line(f"globus task cancel {task_id}")
    assert "cancelled successfully" in result.output


def test_cancel_all_success(run_line):
    """Task cancellation of "all" will pull a task list and call cancel in a loop."""
    num_tasks = 5

    # setup a series of tasks, all with successful cancel responses
    task_ids = [str(uuid.uuid4()) for _ in range(num_tasks)]
    for task_id in task_ids:
        RegisteredResponse(
            service="transfer",
            path=f"/v0.10/task/{task_id}/cancel",
            method="POST",
            json={
                "DATA_TYPE": "result",
                "code": "Canceled",
                "message": "The task has been cancelled successfully.",
                "resource": f"/task/{task_id}/cancel",
                "request_id": "ABCdef789",
            },
        ).add()
    RegisteredResponse(
        service="transfer",
        path="/v0.10/task_list",
        json={
            "DATA_TYPE": "task_list",
            "length": num_tasks,
            "limit": 1000,
            "offset": 0,
            "total": num_tasks,
            # the response is very stubby, just the requisite 'task_id' field
            "DATA": [{"task_id": tid} for tid in task_ids],
        },
    ).add()

    result = run_line("globus task cancel --all")
    assert result.output.count("cancelled successfully") == num_tasks


def test_cancel_all_and_id_mutex(run_line):
    """`--all` and a task ID are mutex args for task cancel."""
    result = run_line(f"globus task cancel --all {uuid.uuid4()}", assert_exit_code=2)
    assert (
        "You must pass EITHER the special --all flag "
        "to cancel all in-progress tasks OR a single "
        "task ID to cancel."
    ) in result.stderr


def test_cancel_all_no_tasks_fails(run_line):
    """`--all` when the list is empty exits early."""
    RegisteredResponse(
        service="transfer",
        path="/v0.10/task_list",
        json={
            "DATA_TYPE": "task_list",
            "length": 0,
            "limit": 1000,
            "offset": 0,
            "total": 0,
            "DATA": [],
        },
    ).add()

    result = run_line("globus task cancel --all", assert_exit_code=1)
    assert "You have no in-progress tasks." in result.stderr


def test_cancel_all_json_output(run_line):
    """`--all -Fjson` produces specially formulated JSON output."""
    num_tasks = 8

    # setup a series of tasks, all with successful cancel responses
    task_ids = [str(uuid.uuid4()) for _ in range(num_tasks)]
    for task_id in task_ids:
        RegisteredResponse(
            service="transfer",
            path=f"/v0.10/task/{task_id}/cancel",
            method="POST",
            json={
                "DATA_TYPE": "result",
                "code": "Canceled",
                "message": "The task has been cancelled successfully.",
                "resource": f"/task/{task_id}/cancel",
                "request_id": "ABCdef789",
            },
        ).add()
    RegisteredResponse(
        service="transfer",
        path="/v0.10/task_list",
        json={
            "DATA_TYPE": "task_list",
            "length": num_tasks,
            "limit": 1000,
            "offset": 0,
            "total": num_tasks,
            # the response is very stubby, just the requisite 'task_id' field
            "DATA": [{"task_id": tid} for tid in task_ids],
        },
    ).add()

    result = run_line("globus task cancel --all --format JSON")
    try:
        output = json.loads(result.output)
    except ValueError:
        pytest.fail(f"cannot load JSON-formatted output: {result.output}")

    assert output["task_ids"] == task_ids
    assert "results" in output
    assert len(output["results"]) == num_tasks
