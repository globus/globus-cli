import uuid

import globus_sdk
import pytest
from globus_sdk._testing import load_response_set, register_response_set
from globus_sdk._testing.data.timer.get_job import JOB_JSON
from globus_sdk._testing.data.timer.get_job import RESPONSES as TIMERS_GET_RESPONSES
from globus_sdk._testing.data.timer.resume_job import (
    RESPONSES as TIMERS_RESUME_RESPONSES,
)


def _urlscope(m: str, s: str) -> str:
    return f"https://auth.globus.org/scopes/{m}/{s}"


@pytest.fixture(scope="session", autouse=True)
def _register_responses(mock_user_data):
    # Note: this value must match so that the mock login data matches the responses
    user_id = mock_user_data["sub"]
    job_id = str(uuid.uuid1())
    collection_id = str(uuid.uuid1())
    transfer_scope = globus_sdk.TransferClient.scopes.all
    timers_scope = globus_sdk.TimerClient.scopes.timer
    transfer_ap_scope = _urlscope("actions.globus.org/transfer", "transfer")
    data_access_scope = _urlscope(collection_id, "data_access")
    full_data_access_scope = (
        f"{transfer_ap_scope}[{transfer_scope}[*{data_access_scope}]]"
    )
    required_scope = f"{timers_scope}[{full_data_access_scope}]"

    metadata = {
        "user_id": user_id,
        "job_id": job_id,
        "collection_id": collection_id,
        "required_scope": required_scope,
    }

    get_job_json_inactive_gare_body = {
        **JOB_JSON,
        "status": "inactive",
        "inactive_reason": {
            "cause": "globus_auth_requirements",
            "detail": {
                "code": "ConsentRequired",
                "authorization_parameters": {
                    "session_message": "Missing required data_access consent",
                    "required_scopes": [required_scope],
                },
            },
        },
    }

    register_response_set(
        "cli.timer_resume.inactive_gare.consents_missing",
        dict(
            get_job=dict(
                service="timer",
                path=f"/jobs/{job_id}",
                method="GET",
                json=get_job_json_inactive_gare_body,
            ),
            resume=dict(
                service="timer",
                path=f"/jobs/{job_id}/resume",
                method="POST",
                json={"message": f"Successfully resumed job {job_id}."},
            ),
            consents=dict(
                service="auth",
                path=f"/v2/api/identities/{user_id}/consents",
                method="GET",
                json={
                    "consents": [
                        {
                            "scope_name": timers_scope,
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
        "cli.timer_resume.inactive_gare.consents_present",
        dict(
            get_job=dict(
                service="timer",
                path=f"/jobs/{job_id}",
                method="GET",
                json=get_job_json_inactive_gare_body,
            ),
            resume=dict(
                service="timer",
                path=f"/jobs/{job_id}/resume",
                method="POST",
                json={"message": f"Successfully resumed job {job_id}."},
            ),
            consents=dict(
                service="auth",
                path=f"/v2/api/identities/{user_id}/consents",
                method="GET",
                json={
                    "consents": [
                        {
                            "scope_name": timers_scope,
                            "dependency_path": [100],
                            "id": 100,
                        },
                        {
                            "scope_name": transfer_ap_scope,
                            "dependency_path": [100, 101],
                            "id": 101,
                        },
                        {
                            "scope_name": transfer_scope,
                            "dependency_path": [100, 101, 102],
                            "id": 102,
                        },
                        {
                            "scope_name": data_access_scope,
                            "dependency_path": [100, 101, 102, 103],
                            "id": 103,
                        },
                    ]
                },
            ),
        ),
        metadata=metadata,
    )


def test_resume_job_active(run_line):
    TIMERS_GET_RESPONSES.activate("default")
    TIMERS_RESUME_RESPONSES.activate("default")
    job_id = TIMERS_GET_RESPONSES.metadata["job_id"]
    run_line(
        ["globus", "timer", "resume", job_id],
        search_stdout=f"Successfully resumed job {job_id}.",
    )


def test_resume_job_inactive_user(run_line):
    TIMERS_GET_RESPONSES.activate("inactive_user")
    TIMERS_RESUME_RESPONSES.activate("default")
    job_id = TIMERS_GET_RESPONSES.metadata["job_id"]
    run_line(
        ["globus", "timer", "resume", job_id],
        search_stdout=f"Successfully resumed job {job_id}.",
    )


def test_resume_job_inactive_gare_consent_missing(run_line):
    meta = load_response_set("cli.timer_resume.inactive_gare.consents_missing").metadata
    job_id = meta["job_id"]
    required_scope = meta["required_scope"]
    result = run_line(
        ["globus", "timer", "resume", job_id],
        assert_exit_code=4,
    )
    assert f"globus session consent '{required_scope}'" in result.output


def test_resume_job_inactive_gare_consent_present(run_line):
    meta = load_response_set("cli.timer_resume.inactive_gare.consents_present").metadata
    job_id = meta["job_id"]
    run_line(
        ["globus", "timer", "resume", job_id],
        search_stdout=f"Successfully resumed job {job_id}.",
    )


def test_resume_job_inactive_gare_consent_missing_but_skip_check(run_line):
    meta = load_response_set("cli.timer_resume.inactive_gare.consents_missing").metadata
    job_id = meta["job_id"]
    run_line(
        ["globus", "timer", "resume", "--skip-inactive-reason-check", job_id],
        search_stdout=f"Successfully resumed job {job_id}.",
    )
