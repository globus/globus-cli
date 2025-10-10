import uuid

import pytest
from globus_sdk.testing import RegisteredResponse


def tests_consent_required_gets_preference_over_authorization_parameters(run_line):
    """
    Confirm that when an error matches both the 'session update' and 'session consent'
    hook rules, we choose the 'session consent' option.

    The likely way for this to happen is a GARE-formatted error for ConsentRequired.
    """
    ep_id = str(uuid.UUID(int=1))

    required_scope = (
        "urn:globus:auth:scope:transfer.api.globus.org:all"
        f"[*https://auth.globus.org/scopes/{ep_id}/data_access]"
    )

    RegisteredResponse(
        service="transfer",
        path=f"/v0.10/operation/endpoint/{ep_id}/ls",
        status=403,
        json={
            "authorization_parameters": {
                "required_scopes": [required_scope],
                "session_message": "Missing required data_access consent",
            },
            "code": "ConsentRequired",
            "message": "Missing required data_access consent",
            "request_id": "m8RfX3cES",
            "required_scopes": [required_scope],
            "resource": f"/operation/endpoint/{ep_id}/ls",
        },
    ).add()
    result = run_line(f"globus ls {ep_id}:/", assert_exit_code=4)
    assert f"globus session consent '{required_scope}'" in result.output


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
        path=f"/v0.10/operation/endpoint/{ep_id}/ls",
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
