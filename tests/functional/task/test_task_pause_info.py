import uuid

from globus_sdk.testing import RegisteredResponse

TASK_ID = str(uuid.UUID(int=0))
RULE_ID = str(uuid.UUID(int=1))
EP_ID = str(uuid.UUID(int=2))
USER_ID = str(uuid.UUID(int=3))

_pause_rule_data = {
    "DATA_TYPE": "pause_rule",
    "id": RULE_ID,
    "message": "SDK Test Pause Rule",
    "start_time": None,
    "endpoint_id": EP_ID,
    "identity_id": None,
    "modified_by_id": USER_ID,
    "created_by_host_manager": False,
    "editable": True,
    "pause_ls": True,
    "pause_mkdir": True,
    "pause_rename": True,
    "pause_task_delete": True,
    "pause_task_transfer_write": True,
    "pause_task_transfer_read": True,
}


def test_show_task_pause_info(run_line):
    RegisteredResponse(
        service="transfer",
        path=f"/v0.10/task/{TASK_ID}/pause_info",
        json={
            "endpoint_display_name": "ExamplePauseEndpoint",
            "message": "This task is like super paused",
            "source_pause_message": None,
            "source_pause_message_share": None,
            "destination_pause_message": None,
            "destination_pause_message_share": None,
            "pause_rules": [_pause_rule_data],
        },
    ).add()
    result = run_line(["globus", "task", "pause-info", TASK_ID])
    assert "write/read/delete/rename/mkdir/ls" in result.output
