import uuid

import globus_sdk
from globus_sdk.scopes import SpecificFlowScopes
from globus_sdk.testing import RegisteredResponse, load_response


def test_create_flow_timer(run_line, userinfo_mocker, logged_in_user_id):
    flow_id = load_response(globus_sdk.FlowsClient.get_flow).metadata["flow_id"]
    load_response(globus_sdk.TimersClient.create_timer, case="flow_timer_success")

    userinfo_meta = userinfo_mocker.configure_unlinked(sub=logged_in_user_id).metadata
    identity_id = userinfo_meta["sub"]
    setup_timer_consent_tree_response(identity_id, flow_id)

    result = run_line(f"globus timer create flow {flow_id} --stop-after-runs=1")

    for field in ("Timer ID", "Type", "Number of Runs", "Schedule"):
        assert f"{field}:" in result.stdout


def setup_timer_consent_tree_response(identity_id, *flow_ids):
    _dummy_consent_fields = {
        "allows_refresh": True,
        "atomically_revocable": False,
        "auto_approved": False,
        "client": str(uuid.UUID(int=1)),
        "created": "1970-01-01T00:00:00.000000+00:00",
        "effective_identity": str(uuid.UUID(int=2)),
        "last_used": "1970-01-01T00:00:00.000000+00:00",
        "status": "approved",
        "updated": "1970-01-01T00:00:00.000000+00:00",
    }
    load_response(
        RegisteredResponse(
            service="auth",
            path=f"/v2/api/identities/{identity_id}/consents",
            method="GET",
            json={
                "consents": [
                    {
                        "scope_name": str(globus_sdk.TimersClient.scopes.timer),
                        "scope": str(uuid.uuid1()),
                        "dependency_path": [200],
                        "id": 200,
                        **_dummy_consent_fields,
                    },
                ]
                + [
                    {
                        "scope_name": str(SpecificFlowScopes(flow_id).user),
                        "scope": str(uuid.uuid1()),
                        "dependency_path": [200, 2000 + idx],
                        "id": 2000 + idx,
                        **_dummy_consent_fields,
                    }
                    for idx, flow_id in enumerate(flow_ids)
                ]
            },
        )
    )
