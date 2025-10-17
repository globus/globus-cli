import uuid

import globus_sdk
import pytest
from globus_sdk.testing import (
    RegisteredResponse,
    load_response,
    load_response_set,
    register_response_set,
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


def test_resume_inactive_run_consent_present(
    run_line, add_flow_login, load_identities_for_flow_run
):
    # setup the response scenario
    response_set = load_response_set("cli.resume_run.inactive_consents_present")
    run_response = response_set.lookup("get_run").json

    flow_id = response_set.metadata["flow_id"]
    run_id = response_set.metadata["run_id"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)
    load_identities_for_flow_run(run_response)

    run_line(
        ["globus", "flows", "run", "resume", run_id],
        search_stdout=[("Flow ID", flow_id), ("Run ID", run_id)],
    )


def test_resume_inactive_run_consent_missing_but_skip_check(
    run_line, add_flow_login, load_identities_for_flow_run
):
    # setup the response scenario
    response_set = load_response_set("cli.resume_run.inactive_consents_missing")
    run_response = response_set.lookup("get_run").json

    flow_id = response_set.metadata["flow_id"]
    run_id = response_set.metadata["run_id"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)
    load_identities_for_flow_run(run_response)

    run_line(
        ["globus", "flows", "run", "resume", run_id, "--skip-inactive-reason-check"],
        search_stdout=[("Flow ID", flow_id), ("Run ID", run_id)],
    )


def test_resume_inactive_run_session_identities(
    run_line, add_flow_login, load_identities_for_flow_run
):
    # setup the response scenario
    response_set = load_response_set("cli.resume_run.inactive_session_identities")
    run_response = response_set.lookup("get_run").json

    flow_id = response_set.metadata["flow_id"]
    run_id = response_set.metadata["run_id"]
    username = response_set.metadata["username"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)
    load_identities_for_flow_run(run_response)

    run_line(
        ["globus", "flows", "run", "resume", run_id],
        assert_exit_code=4,
        search_stdout=f"globus session update {username}",
    )


def test_resume_inactive_run_session_identities_but_skip_check(
    run_line, add_flow_login, load_identities_for_flow_run
):
    # setup the response scenario
    response_set = load_response_set("cli.resume_run.inactive_session_identities")
    run_response = response_set.lookup("get_run").json

    flow_id = response_set.metadata["flow_id"]
    run_id = response_set.metadata["run_id"]

    # setup the login mock for the flow_id as well
    add_flow_login(flow_id)
    load_identities_for_flow_run(run_response)

    run_line(
        ["globus", "flows", "run", "resume", run_id, "--skip-inactive-reason-check"],
        search_stdout=[("Flow ID", flow_id), ("Run ID", run_id)],
    )


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
    full_data_access_scope = transfer_scope.with_dependency(
        data_access_scope.with_optional(True)
    )
    required_scope = flow_scope.with_dependency(full_data_access_scope)
    username = "shrek@fairytale"

    metadata = {
        "user_id": user_id,
        "username": username,
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
                        "required_scope": str(full_data_access_scope),
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
            "required_scope": str(required_scope),
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
    inactive_required_session_identities_body = {
        "action_id": run_id,
        "created_by": user_urn,
        "details": {
            "action_statuses": [
                {
                    "action_id": "1IcYClstkVzjn",
                    "creator_id": user_urn,
                    "details": {
                        "code": "AuthorizationParameters",
                        "description": f"Need a login with {username}",
                        "authorization_parameters": {
                            "session_required_identities": [username]
                        },
                    },
                    "state_name": "authn",
                    "status": "INACTIVE",
                }
            ],
            "code": "AuthorizationParameters",
            "description": "Go to Tosche Station to pick up some power converters.",
            "authorization_parameters": {
                "session_message": f"Need a login with {username}",
                "session_required_identities": [username],
            },
            "state_name": "authn",
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
    register_response_set(
        "cli.resume_run.inactive_consents_missing",
        {
            "get_run": {
                "service": "flows",
                "path": f"/runs/{run_id}",
                "json": inactive_consent_required_body,
            },
            "resume": {
                "service": "flows",
                "path": f"/runs/{run_id}/resume",
                "method": "POST",
                "json": succeeded_body,
            },
            "consents": {
                "service": "auth",
                "path": f"/v2/api/identities/{user_id}/consents",
                "method": "GET",
                "json": {
                    "consents": [
                        {
                            "scope_name": str(flow_scope),
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100],
                            "id": 100,
                            **_dummy_consent_fields,
                        }
                    ]
                },
            },
        },
        metadata=metadata,
    )

    register_response_set(
        "cli.resume_run.inactive_consents_present",
        {
            "get_run": {
                "service": "flows",
                "path": f"/runs/{run_id}",
                "json": inactive_consent_required_body,
            },
            "resume": {
                "service": "flows",
                "path": f"/runs/{run_id}/resume",
                "method": "POST",
                "json": succeeded_body,
            },
            "consents": {
                "service": "auth",
                "path": f"/v2/api/identities/{user_id}/consents",
                "method": "GET",
                "json": {
                    "consents": [
                        {
                            "scope_name": str(flow_scope),
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100],
                            "id": 100,
                            **_dummy_consent_fields,
                        },
                        {
                            "scope_name": str(transfer_scope),
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100, 101],
                            "id": 101,
                            **_dummy_consent_fields,
                        },
                        {
                            "scope_name": str(data_access_scope),
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100, 101, 102],
                            "id": 102,
                            **_dummy_consent_fields,
                        },
                    ]
                },
            },
        },
        metadata=metadata,
    )

    register_response_set(
        "cli.resume_run.inactive_session_identities",
        {
            "get_run": {
                "service": "flows",
                "path": f"/runs/{run_id}",
                "json": inactive_required_session_identities_body,
            },
            "resume": {
                "service": "flows",
                "path": f"/runs/{run_id}/resume",
                "method": "POST",
                "json": succeeded_body,
            },
        },
        metadata=metadata,
    )


def test_resume_run_text_output(run_line, add_flow_login, load_identities_for_flow_run):
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
            json={"flow_id": flow_id},
        )
    )

    # setup the login mock for that flow_id as well, so that we can
    # get a SpecificFlowClient for this flow
    add_flow_login(flow_id)

    load_identities_for_flow_run(response_payload)

    run_line(
        ["globus", "flows", "run", "resume", run_id],
        search_stdout=[
            ("Flow ID", flow_id),
            ("Run ID", run_id),
            ("Run Tags", ", ".join(tags)),
            ("Run Label", label),
            ("Status", status),
            ("Flow Title", flow_title),
        ],
    )


def _urlscope(m: str, s: str) -> str:
    return globus_sdk.Scope(f"https://auth.globus.org/scopes/{m}/{s}")
