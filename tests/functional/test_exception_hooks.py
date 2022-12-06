import uuid

from globus_sdk._testing import RegisteredResponse, load_response, load_response_set


def test_session_required_policies(run_line):
    """
    ls on hits a 403 with session_required_policies set
    confirms correct globus session update command in helptext
    """
    meta = load_response_set("cli.transfer_activate_success").metadata
    ep_id = meta["endpoint_id"]
    policy_id = str(uuid.uuid4())

    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/operation/endpoint/{ep_id}/ls",
            status=403,
            json={
                "authorization_parameters": {
                    "session_message": "Failing collection authentication policy",
                    "session_required_policies": policy_id,
                },
                "code": "AuthPolicyFailed",
                "message": "Failing collection authentication policy",
                "request_id": "MSbPbMR9n",
                "resource": f"/operation/endpoint/{ep_id}/ls",
            },
        )
    )
    result = run_line(f"globus ls {ep_id}:/", assert_exit_code=4)

    assert f"globus session update --policy {policy_id}" in result.output
