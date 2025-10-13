import json

import pytest
import responses
from globus_sdk.testing import load_response, register_response_set


@pytest.fixture(autouse=True, scope="session")
def _register_invitation_responses():
    group_id = "ee49e222-d007-11e4-8b51-22000aa51e6e"
    identity_id = "00000000-0000-0000-0000-000000000001"
    username = "test_user1"
    identity_id2 = "00000000-0000-0000-0000-000000000002"
    username2 = "test_user2"

    _group_common = {
        "description": "Un film Italiano muy bien conocido",
        "enforce_session": False,
        "group_type": "regular",
        "id": group_id,
        "name": "La Dolce Vita",
        "parent_id": None,
        "policies": {
            "authentication_assurance_timeout": 28800,
            "group_members_visibility": "managers",
            "group_visibility": "authenticated",
            "is_high_assurance": False,
            "join_requests": False,
            "signup_fields": [],
        },
        "session_limit": 28800,
        "session_timeouts": {},
    }
    _common_metadata = {
        "group_id": group_id,
        "identity_id": identity_id,
        "username": username,
        "identity_id2": identity_id2,
        "username2": username2,
    }

    register_response_set(
        "group_to_leave",
        {
            "default": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {
                    "my_memberships": [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "membership_fields": {},
                            "role": "member",
                            "status": "active",
                            "username": username,
                        },
                    ],
                    **_group_common,
                },
                "metadata": _common_metadata,
            },
            "multiple": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {
                    "my_memberships": [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "membership_fields": {},
                            "role": "admin",
                            "status": "active",
                            "username": username,
                        },
                        {
                            "group_id": group_id,
                            "identity_id": identity_id2,
                            "membership_fields": {},
                            "role": "member",
                            "status": "active",
                            "username": username2,
                        },
                    ],
                    **_group_common,
                },
                "metadata": _common_metadata,
            },
            "not_member": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {
                    "my_memberships": [],
                    **_group_common,
                },
                "metadata": _common_metadata,
            },
        },
        metadata=_common_metadata,
    )

    def leave_response(*, status="success", error_detail_present=True, add_ids=None):
        identities = [identity_id]
        if add_ids:
            identities += add_ids
        return {
            "service": "groups",
            "path": f"/v2/groups/{group_id}",
            "method": "POST",
            "json": (
                {
                    "leave": [
                        {
                            "group_id": group_id,
                            "identity_id": iid,
                            "username": username,
                            "role": "member",
                            "status": "active",
                        }
                        for iid in identities
                    ]
                }
                if status == "success"
                else (
                    {
                        "leave": [],
                        "errors": {
                            "leave": [
                                {
                                    "code": "ERROR_ERROR_IT_IS_AN_ERROR",
                                    "identity_id": iid,
                                    **(
                                        {"detail": "Domo arigato, Mr. Roboto"}
                                        if error_detail_present
                                        else {}
                                    ),
                                }
                                for iid in identities
                            ]
                        },
                    }
                    if status == "error"
                    else {
                        "leave": [
                            {
                                "group_id": group_id,
                                "identity_id": iid,
                                "username": username,
                                "role": "member",
                                "status": "active",
                            }
                            for iid in identities
                            if iid != identity_id
                        ],
                        "errors": {
                            "leave": [
                                {
                                    "code": "ERROR_ERROR_IT_IS_AN_ERROR",
                                    "identity_id": identity_id,
                                    **(
                                        {"detail": "Domo arigato, Mr. Roboto"}
                                        if error_detail_present
                                        else {}
                                    ),
                                }
                            ]
                        },
                    }
                )
            ),
            "metadata": _common_metadata,
        }

    register_response_set(
        "group_leave_response",
        {
            "default": leave_response(),
            "multiple": leave_response(add_ids=[identity_id2]),
            "error": leave_response(status="error"),
            "error_nodetail": leave_response(
                status="error", error_detail_present=False
            ),
            "partial_error": leave_response(status="partial", add_ids=[identity_id2]),
            "partial_error_nodetail": leave_response(
                status="partial", add_ids=[identity_id2], error_detail_present=False
            ),
        },
        metadata=_common_metadata,
    )


@pytest.mark.parametrize("with_id_arg", (True, False))
def test_group_leave(run_line, with_id_arg):
    meta = load_response("group_leave_response").metadata
    load_response("group_to_leave")

    add_args = []
    if with_id_arg:
        add_args = ["--identity", meta["identity_id"]]
    result = run_line(["globus", "group", "leave", meta["group_id"]] + add_args)
    assert meta["identity_id"] in result.output
    assert meta["identity_id2"] not in result.output

    sent_data = json.loads(responses.calls[-1].request.body)
    assert "leave" in sent_data
    assert len(sent_data["leave"]) == 1
    assert sent_data["leave"][0]["identity_id"] == meta["identity_id"]


def test_group_leave_multi_membership(run_line):
    meta = load_response("group_leave_response", case="multiple").metadata
    load_response("group_to_leave", case="multiple")

    result = run_line(["globus", "group", "leave", meta["group_id"]])
    assert meta["identity_id"] in result.output
    assert meta["identity_id2"] in result.output

    sent_data = json.loads(responses.calls[-1].request.body)
    assert "leave" in sent_data
    assert len(sent_data["leave"]) == 2
    assert {x["identity_id"] for x in sent_data["leave"]} == {
        meta["identity_id"],
        meta["identity_id2"],
    }


@pytest.mark.parametrize("error_detail_present", (True, False))
def test_group_leave_failure(run_line, error_detail_present):
    load_response("group_to_leave")
    meta = load_response(
        "group_leave_response",
        case="error" if error_detail_present else "error_nodetail",
    ).metadata

    result = run_line(
        ["globus", "group", "leave", meta["group_id"]], assert_exit_code=1
    )
    assert "Error" in result.stderr
    if error_detail_present:
        assert "Domo arigato" in result.stderr
    else:
        assert "Could not leave group" in result.stderr

    # the request sent was as expected
    sent_data = json.loads(responses.calls[-1].request.body)
    assert "leave" in sent_data
    assert len(sent_data["leave"]) == 1
    assert sent_data["leave"][0]["identity_id"] == meta["identity_id"]


@pytest.mark.parametrize("error_detail_present", (True, False))
def test_group_leave_partial_failure(run_line, error_detail_present):
    load_response("group_to_leave", case="multiple")
    meta = load_response(
        "group_leave_response",
        case="partial_error" if error_detail_present else "partial_error_nodetail",
    ).metadata

    result = run_line(["globus", "group", "leave", meta["group_id"]])
    assert "Encountered errors leaving group, partial success" in result.output
    if error_detail_present:
        assert meta["identity_id"] in result.output
    else:
        assert meta["identity_id"] not in result.output
    assert meta["identity_id2"] in result.output

    if error_detail_present:
        assert "error: Domo arigato" in result.output
    else:
        assert "error: <<no detail>>" in result.output


def test_group_leave_failure_not_a_member(run_line):
    meta = load_response("group_to_leave", case="not_member").metadata
    result = run_line(
        ["globus", "group", "leave", meta["group_id"]], assert_exit_code=1
    )
    assert "You have no memberships" in result.stderr
