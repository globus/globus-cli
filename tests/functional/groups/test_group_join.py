import json
import uuid

import pytest
import responses
from globus_sdk.testing import load_response, register_response_set


@pytest.fixture(autouse=True, scope="session")
def _register_invitation_responses():
    group_id = str(uuid.uuid4())
    identity_id = str(uuid.UUID(int=1))
    username = "test_user1"

    _common_metadata = {
        "group_id": group_id,
        "identity_id": identity_id,
        "username": username,
    }

    def action_response(action: str, success, *, error_detail_present=True):
        return {
            "service": "groups",
            "path": f"/v2/groups/{group_id}",
            "method": "POST",
            "json": (
                {
                    action: [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "username": username,
                            "role": "member",
                            "status": "active",
                        }
                    ]
                }
                if success
                else {
                    action: [],
                    "errors": {
                        action: [
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
            ),
            "metadata": _common_metadata,
        }

    for action in ("join", "request_join"):
        register_response_set(
            f"group_{action}_response",
            {
                "default": action_response(action, True),
                "error": action_response(action, False),
                "error_nodetail": action_response(
                    action, False, error_detail_present=False
                ),
            },
            metadata=_common_metadata,
        )


@pytest.mark.parametrize("action", ("join", "request_join"))
@pytest.mark.parametrize("with_id_arg", (True, False))
def test_group_join(run_line, userinfo_mocker, action, with_id_arg):
    meta = load_response(f"group_{action}_response").metadata
    userinfo_mocker.configure_unlinked(sub=meta["identity_id"])

    add_args = []
    if with_id_arg:
        add_args = ["--identity", meta["identity_id"]]
    if action == "request_join":
        add_args.append("--request")
    result = run_line(["globus", "group", "join", meta["group_id"]] + add_args)
    assert meta["identity_id"] in result.output

    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == meta["identity_id"]


@pytest.mark.parametrize("action", ("join", "request_join"))
@pytest.mark.parametrize("error_detail_present", (True, False))
def test_group_join_failure(run_line, userinfo_mocker, action, error_detail_present):
    meta = load_response(
        f"group_{action}_response",
        case="error" if error_detail_present else "error_nodetail",
    ).metadata
    userinfo_mocker.configure_unlinked(sub=meta["identity_id"])

    add_args = []
    if action == "request_join":
        add_args.append("--request")
    result = run_line(
        ["globus", "group", "join", meta["group_id"]] + add_args, assert_exit_code=1
    )
    assert "Error" in result.stderr
    if error_detail_present:
        assert "Domo arigato" in result.stderr
    else:
        assert "Could not join group" in result.stderr

    # the request sent was as expected
    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == meta["identity_id"]
