import json

import pytest
from globus_sdk._testing import get_last_request, load_response_set


@pytest.mark.parametrize(
    "add_args, payload_contains",
    (
        (("--name", "New Name"), {"name": "New Name"}),
        (("--description", "New Description"), {"description": "New Description"}),
        (
            ("--terms-and-conditions", "New Terms and Conditions"),
            {"terms_and_conditions": "New Terms and Conditions"},
        ),
        (
            (
                "--name",
                "New Name",
                "--description",
                "New Description",
                "--terms-and-conditions",
                "New Terms and Conditions",
            ),
            {
                "description": "New Description",
                "name": "New Name",
                "terms_and_conditions": "New Terms and Conditions",
            },
        ),
    ),
)
def test_group_update(run_line, add_args, payload_contains):
    """
    Basic success test for globus group update
    Confirms existing values are included in the put document when
    not specified by options
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]
    group1_name = meta["group1_name"]
    group1_description = meta["group1_description"]

    # update name
    result = run_line(("globus", "group", "update", group1_id) + add_args)
    assert "Group updated successfully" in result.output

    # confirm that 'name' and 'description' are both always sent,
    # either with the new values or with their pre-existing values
    last_req = get_last_request()
    sent = json.loads(last_req.body)
    if "name" in payload_contains:
        assert sent["name"] == payload_contains["name"]
    else:
        assert sent["name"] == group1_name
    if "description" in payload_contains:
        assert sent["description"] == payload_contains["description"]
    else:
        assert sent["description"] == group1_description
