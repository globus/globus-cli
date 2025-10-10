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

    def action_response(
        action: str, success, *, error_detail_present=True, add_ids=None
    ):
        identities = [identity_id]
        if add_ids:
            identities += add_ids
        return {
            "service": "groups",
            "path": f"/groups/{group_id}",
            "method": "POST",
            "json": (
                {
                    action: [
                        {
                            "group_id": group_id,
                            "identity_id": iid,
                            "username": (
                                username
                                if iid == identity_id
                                else username2 if iid == identity_id2 else "foo-user"
                            ),
                            "role": "member",
                            "status": "active" if action == "accept" else "declined",
                        }
                        for iid in identities
                    ]
                }
                if success
                else {
                    action: [],
                    "errors": {
                        action: [
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
            ),
        }

    register_response_set(
        "group_w_invitation",
        {
            "default": {
                "service": "groups",
                "path": f"/groups/{group_id}",
                "json": {
                    "my_memberships": [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "membership_fields": {},
                            "role": "member",
                            "status": "invited",
                            "username": username,
                        },
                    ],
                    **_group_common,
                },
                "metadata": _common_metadata,
            },
            "multiple": {
                "service": "groups",
                "path": f"/groups/{group_id}",
                "json": {
                    "my_memberships": [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "membership_fields": {},
                            "role": "member",
                            "status": "invited",
                            "username": username,
                        },
                        {
                            "group_id": group_id,
                            "identity_id": identity_id2,
                            "membership_fields": {},
                            "role": "member",
                            "status": "invited",
                            "username": username2,
                        },
                    ],
                    **_group_common,
                },
                "metadata": _common_metadata,
            },
        },
        metadata=_common_metadata,
    )
    register_response_set(
        "group_wo_invitation",
        {
            "default": {
                "service": "groups",
                "path": f"/groups/{group_id}",
                "json": {"my_memberships": [], **_group_common},
                "metadata": _common_metadata,
            }
        },
        metadata=_common_metadata,
    )
    register_response_set(
        "group_accept_response",
        {
            "default": action_response("accept", True),
            "success_multiple": action_response("accept", True, add_ids=[identity_id2]),
            "error": action_response("accept", False),
            "error_multiple": action_response("accept", False, add_ids=[identity_id2]),
            "error_nodetail": action_response(
                "accept", False, error_detail_present=False
            ),
        },
        metadata=_common_metadata,
    )
    register_response_set(
        "group_decline_response",
        {
            "default": action_response("decline", True),
            "success_multiple": action_response(
                "decline", True, add_ids=[identity_id2]
            ),
            "error": action_response("decline", False),
            "error_multiple": action_response("decline", False, add_ids=[identity_id2]),
            "error_nodetail": action_response(
                "decline", False, error_detail_present=False
            ),
        },
        metadata=_common_metadata,
    )


@pytest.mark.parametrize("action", ("accept", "decline"))
@pytest.mark.parametrize("with_id_arg", (True, False))
def test_group_invite(run_line, action, with_id_arg):
    meta = load_response("group_w_invitation").metadata
    load_response(f"group_{action}_response")

    add_args = []
    if with_id_arg:
        add_args = ["--identity", meta["identity_id"]]
    result = run_line(
        ["globus", "group", "invite", action, meta["group_id"]] + add_args
    )
    assert meta["identity_id"] in result.output

    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == meta["identity_id"]


@pytest.mark.parametrize("action", ("accept", "decline"))
@pytest.mark.parametrize("error_detail_present", (True, False))
def test_group_invite_failure(run_line, action, error_detail_present):
    meta = load_response("group_w_invitation").metadata
    load_response(
        f"group_{action}_response",
        case="error" if error_detail_present else "error_nodetail",
    )

    result = run_line(
        ["globus", "group", "invite", action, meta["group_id"]], assert_exit_code=1
    )
    assert "Error" in result.stderr
    if error_detail_present:
        assert "Domo arigato" in result.stderr
    else:
        assert f"Could not {action} invite" in result.stderr

    # the request sent was as expected
    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == meta["identity_id"]


@pytest.mark.parametrize("action", ("accept", "decline"))
def test_group_invite_failure_no_invitation(run_line, action):
    meta = load_response("group_wo_invitation").metadata
    result = run_line(
        ["globus", "group", "invite", action, meta["group_id"]], assert_exit_code=1
    )
    assert "You have no invitations" in result.stderr
    # only one request sent (get group)
    assert len(responses.calls) == 1


@pytest.mark.parametrize("action", ("accept", "decline"))
@pytest.mark.parametrize("success", (True, False))
def test_group_invite_multiple(run_line, action, success):
    meta = load_response("group_w_invitation", case="multiple").metadata
    load_response(
        f"group_{action}_response", case=f"{'success' if success else 'error'}_multiple"
    )

    result = run_line(
        ["globus", "group", "invite", action, meta["group_id"]],
        assert_exit_code=0 if success else 1,
    )
    if success:
        if action == "accept":
            assert "Accepted invitation as" in result.output
        else:
            assert "Declined invitation as" in result.output
        assert meta["identity_id"] in result.output
        assert meta["identity_id2"] in result.output
        assert meta["username"] in result.output
        assert meta["username2"] in result.output
    else:
        assert "Error" in result.stderr
        assert "Domo arigato" in result.stderr

    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 2
    assert {x["identity_id"] for x in sent_data[action]} == {
        meta["identity_id"],
        meta["identity_id2"],
    }
