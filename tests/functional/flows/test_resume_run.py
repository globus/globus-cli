import uuid

import globus_sdk
import pytest
from globus_sdk._testing import (
    RegisteredResponse,
    load_response,
    load_response_set,
    register_response_set,
)


def _urlscope(m: str, s: str) -> str:
    return f"https://auth.globus.org/scopes/{m}/{s}"


@pytest.fixture(scope="session", autouse=True)
def _register_responses(mock_user_data):
    # Note: this value must match so that the mock login data matches the responses
    user_id = mock_user_data["sub"]

    user_urn = f"urn:globus:auth:identity:{user_id}"
    flow_id = str(uuid.uuid1())
    run_id = str(uuid.uuid1())
    collection_id = str(uuid.uuid1())
    transfer_scope = globus_sdk.TransferClient.scopes.all
    flow_scope = _urlscope(flow_id, f"flow_{flow_id.replace('-', '_')}_user")
    data_access_scope = _urlscope(collection_id, "data_access")
    full_data_access_scope = (
        f"{transfer_scope}[*{_urlscope(collection_id, 'data_access')}]"
    )
    required_scope = f"{flow_scope}[{full_data_access_scope}]"

    metadata = {
        "user_id": user_id,
        "flow_id": flow_id,
        "run_id": run_id,
        "collection_id": collection_id,
        "required_scope": required_scope,
    }

    inactive_consent_required_body = {
        "action_id": run_id,
        "created_by": user_urn,
        "details": {
            "action_statuses": [
                {
                    "action_id": "1IcYClstkVzjn",
                    "completion_time": "2023-08-07T17:24:10.681615+00:00",
                    "creator_id": user_urn,
                    "details": {
                        "code": "ConsentRequired",
                        "description": "Missing required data_access consent",
                        "required_scope": full_data_access_scope,
                        "resolution_url": None,
                    },
                    "display_status": "INACTIVE",
                    "label": None,
                    "manage_by": [],
                    "monitor_by": [],
                    "release_after": "P30D",
                    "start_time": "2023-08-07 17:24:10.681600+00:00",
                    "state_name": "Transfer",
                    "status": "INACTIVE",
                }
            ],
            "code": "ConsentRequired",
            "description": "Go to Tosche Station to pick up some power converters.",
            "required_scope": required_scope,
            "state_name": "GetPermissionFromUncleOwen",
        },
        "display_status": "INACTIVE",
        "flow_id": flow_id,
        "flow_last_updated": "2023-08-02T17:20:17.442007+00:00",
        "flow_title": "Convert Power",
        "label": "you can waste time with your friends when your chores are done",
        "manage_by": [],
        "monitor_by": [],
        "run_id": run_id,
        "run_managers": [],
        "run_monitors": [],
        "run_owner": user_urn,
        "start_time": "2023-08-07T17:24:03.315708+00:00",
        "status": "INACTIVE",
        "tags": ["tatooine"],
        "user_role": "run_owner",
    }
    succeeded_body = {
        "run_id": run_id,
        "action_id": run_id,
        "completion_time": "2023-08-09T17:24:03.315708+00:00",
        "created_by": user_id,
        "details": {
            "code": "FlowSucceeded",
            "description": "Got permission and went to Tosche Station",
        },
        "display_status": "SUCCEEDED",
        "flow_id": flow_id,
        "flow_last_updated": "2023-04-11T20:00:06.524930+00:00",
        "flow_title": "Convert Power",
        "label": "you can waste time with your friends when your chores are done",
        "manage_by": [],
        "monitor_by": [],
        "run_managers": [],
        "run_monitors": [],
        "run_owner": user_urn,
        "start_time": "2023-04-11T20:01:18.040416+00:00",
        "status": "SUCCEEDED",
        "tags": ["tatooine"],
        "user_role": "run_owner",
    }

    register_response_set(
        "cli.resume_run.inactive_consents_missing",
        dict(
            get_run=dict(
                service="flows",
                path=f"/runs/{run_id}",
                json=inactive_consent_required_body,
            ),
            resume=dict(
                service="flows",
                path=f"/runs/{run_id}/resume",
                method="POST",
                json=succeeded_body,
            ),
            consents=dict(
                service="auth",
                path=f"/v2/api/identities/{user_id}/consents",
                method="GET",
                json={
                    "consents": [
                        {
                            "scope_name": flow_scope,
                            "dependency_path": [100],
                            "id": 100,
                        }
                    ]
                },
            ),
        ),
        metadata=metadata,
    )

    register_response_set(
        "cli.resume_run.inactive_consents_present",
        dict(
            get_run=dict(
                service="flows",
                path=f"/runs/{run_id}",
                json=inactive_consent_required_body,
            ),
            resume=dict(
                service="flows",
                path=f"/runs/{run_id}/resume",
                method="POST",
                json=succeeded_body,
            ),
            consents=dict(
                service="auth",
                path=f"/v2/api/identities/{user_id}/consents",
                method="GET",
                json={
                    "consents": [
                        {
                            "scope_name": flow_scope,
                            "dependency_path": [100],
                            "id": 100,
                        },
                        {
                            "scope_name": transfer_scope,
                            "dependency_path": [100, 101],
                            "id": 101,
                        },
                        {
                            "scope_name": data_access_scope,
                            "dependency_path": [100, 101, 102],
                            "id": 102,
                        },
                    ]
                },
            ),
        ),
        metadata=metadata,
    )


def test_resume_run_text_output(run_line, add_flow_login):
    # get fields for resume_run
    response = load_response("flows.resume_run")
    meta = response.metadata
    response_payload = response.json
    flow_id = meta["flow_id"]
    run_id = meta["run_id"]
    tags = response_payload["tags"]
    label = response_payload["label"]
    status = response_payload["status"]
    flow_title = response_payload["flow_title"]

    # setup a GET /runs/{run_id} mock
    # it only needs to return a matching flow_id
    # (NB: the mock for 'flows.get_run' does not have the same run_id)
    load_response(
        RegisteredResponse(
            service="flows",
            method="get",
            path=f"/runs/{run_id}",
            json={
                "flow_id": flow_id,
            },
        )
    )

    # setup the login mock for that flow_id as well, so that we can
    # get a SpecificFlowClient for this flow
    add_flow_login(flow_id)

    run_line(
        ["globus", "flows", "run", "resume", run_id],
        search_stdout=[
            ("Flow ID", flow_id),
            ("Run ID", run_id),
            ("Run Tags", ",".join(tags)),
            ("Run Label", label),
            ("Status", status),
            ("Flow Title", flow_title),
        ],
    )


def test_resume_inactive_run_missing_consent(run_line, add_flow_login):
    # setup the response scenario
    meta = load_response_set("cli.resume_run.inactive_consents_missing").metadata
    flow_id = meta["flow_id"]
    run_id = meta["run_id"]
    required_scope = meta["required_scope"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)

    result = run_line(["globus", "flows", "run", "resume", run_id], assert_exit_code=4)
    assert f"globus session consent '{required_scope}'" in result.output


def test_resume_inactive_run_consent_present(run_line, add_flow_login):
    # setup the response scenario
    meta = load_response_set("cli.resume_run.inactive_consents_present").metadata
    flow_id = meta["flow_id"]
    run_id = meta["run_id"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)

    run_line(
        ["globus", "flows", "run", "resume", run_id],
        search_stdout=[("Flow ID", flow_id), ("Run ID", run_id)],
    )


def test_resume_inactive_run_consent_missing_but_skip_check(run_line, add_flow_login):
    # setup the response scenario
    meta = load_response_set("cli.resume_run.inactive_consents_missing").metadata
    flow_id = meta["flow_id"]
    run_id = meta["run_id"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)

    run_line(
        ["globus", "flows", "run", "resume", run_id, "--skip-inactive-reason-check"],
        search_stdout=[("Flow ID", flow_id), ("Run ID", run_id)],
    )
