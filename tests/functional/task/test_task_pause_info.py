import uuid

import pytest
from globus_sdk.testing import load_response, register_response_set

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


@pytest.fixture(autouse=True, scope="session")
def _register_pause_rule_responses():
    register_response_set(
        "task_pause_info",
        {
            "default": {
                "service": "transfer",
                "path": f"/task/{TASK_ID}/pause_info",
                "json": {
                    "endpoint_display_name": "ExamplePauseEndpoint",
                    "message": "This task is like super paused",
                    "source_pause_message": None,
                    "source_pause_message_share": None,
                    "destination_pause_message": None,
                    "destination_pause_message_share": None,
                    "pause_rules": [_pause_rule_data],
                },
            }
        },
        metadata={
            "task_id": TASK_ID,
            "rule_id": RULE_ID,
            "endpoint_id": EP_ID,
            "pause_rule_modified_by": USER_ID,
        },
    )


def test_show_task_pause_info(run_line):
    meta = load_response("task_pause_info").metadata
    result = run_line(["globus", "task", "pause-info", meta["task_id"]])
    assert "write/read/delete/rename/mkdir/ls" in result.output
