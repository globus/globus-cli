import json
import uuid

import pytest
from globus_sdk.testing import get_last_request, load_response_set


@pytest.mark.parametrize("parent_group_id", (None, str(uuid.UUID(int=0))))
def test_group_create(run_line, parent_group_id):
    """
    Basic success test for globus group create.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]
    group1_name = meta["group1_name"]
    group1_description = meta["group1_description"]

    cmd = [
        "globus",
        "group",
        "create",
        group1_name,
        "--description",
        group1_description,
    ]
    if parent_group_id:
        cmd.extend(["--parent-id", parent_group_id])
    result = run_line(cmd)

    assert f"Group {group1_id} created successfully" in result.output

    last_req = get_last_request()
    sent = json.loads(last_req.body)
    assert sent["parent_id"] == parent_group_id
