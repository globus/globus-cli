import json

import pytest
from globus_sdk._testing import (
    get_last_request,
    load_response_set,
    register_response_set,
)


@pytest.fixture(autouse=True, scope="session")
def _register_group_responses():
    group_id = "ca3c5adc-a0ba-11ec-b51e-91e0c9a2d44f"

    register_response_set(
        "get_and_set_group_policies",
        {
            "get_group_policies": {
                "service": "groups",
                "path": f"/groups/{group_id}/policies",
                "json": {
                    "is_high_assurance": False,
                    "authentication_assurance_timeout": 28800,
                    "group_visibility": "private",
                    "group_members_visibility": "managers",
                    "join_requests": False,
                    "signup_fields": [],
                },
            },
            "set_group_policies": {
                "service": "groups",
                "method": "PUT",
                "path": f"/groups/{group_id}/policies",
                "json": {"foo": "bar"},
            },
        },
        metadata={
            "group_id": group_id,
        },
    )


@pytest.mark.parametrize(
    "add_args, field_name, expected_value",
    [
        (["--high-assurance"], "is_high_assurance", True),
        (["--no-high-assurance"], "is_high_assurance", False),
        (["--authentication-timeout", "100"], "authentication_assurance_timeout", 100),
        (["--visibility", "authenticated"], "group_visibility", "authenticated"),
        (["--members-visibility", "members"], "group_members_visibility", "members"),
        (["--join-requests"], "join_requests", True),
        (["--no-join-requests"], "join_requests", False),
        (["--signup-fields", "address"], "signup_fields", ["address"]),
        (
            ["--signup-fields", "address1,address2"],
            "signup_fields",
            ["address1", "address2"],
        ),
    ],
)
def test_group_set_policies(run_line, add_args, field_name, expected_value):
    fixtures = load_response_set("get_and_set_group_policies")
    group_id = fixtures.metadata["group_id"]

    result = run_line(["globus", "group", "set-policies", group_id] + add_args)
    assert "Group policies updated successfully" in result.output

    last_req = get_last_request()
    body = json.loads(last_req.body)

    # confirm expected put body values
    get_response = fixtures.lookup("get_group_policies")
    for field, value in body.items():
        if field != field_name:
            assert value == get_response.json[field]
        else:
            assert value == expected_value
