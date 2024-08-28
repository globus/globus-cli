import uuid

import pytest
from globus_sdk._testing import RegisteredResponse


@pytest.mark.parametrize("num_policies", (1, 3))
def test_session_required_policies(run_line, num_policies):
    """
    confirms a correct `globus session update` command is shown in helptext
    after hitting a 403 with session_required_policies set
    """
    ep_id = str(uuid.UUID(int=1))
    policies = ",".join(str(uuid.uuid4()) for _ in range(num_policies))

    RegisteredResponse(
        service="transfer",
        path=f"/operation/endpoint/{ep_id}/ls",
        status=403,
        json={
            "authorization_parameters": {
                "session_message": "Failing collection authentication policy",
                "session_required_policies": policies,
            },
            "code": "AuthPolicyFailed",
            "message": "Failing collection authentication policy",
            "request_id": "MSbPbMR9n",
            "resource": f"/operation/endpoint/{ep_id}/ls",
        },
    ).add()
    result = run_line(f"globus ls {ep_id}:/", assert_exit_code=4)

    assert f"globus session update --policy '{policies}'" in result.output
