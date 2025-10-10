import uuid

import globus_sdk
import pytest
from globus_sdk.testing import load_response, load_response_set, register_response_set


def test_resume_timer_active(run_line):
    meta = load_response("timer.get_job").metadata
    load_response("timer.resume_job")
    timer_id = meta["job_id"]
    run_line(
        ["globus", "timer", "resume", timer_id],
        search_stdout=f"Successfully resumed job {timer_id}.",
    )


def test_resume_timer_inactive_user(run_line):
    meta = load_response("timer.get_job", case="inactive_user").metadata
    load_response("timer.resume_job")
    timer_id = meta["job_id"]
    run_line(
        ["globus", "timer", "resume", timer_id],
        search_stdout=f"Successfully resumed job {timer_id}.",
    )


def test_resume_timer_inactive_gare_consent_missing(run_line):
    meta = load_response_set("cli.timer_resume.inactive_gare.consents_missing").metadata
    timer_id = meta["timer_id"]
    required_scope = meta["required_scope"]
    result = run_line(
        ["globus", "timer", "resume", timer_id],
        assert_exit_code=4,
    )
    assert f"globus session consent '{required_scope}'" in result.output


def test_resume_timer_inactive_gare_consent_present(run_line):
    meta = load_response_set("cli.timer_resume.inactive_gare.consents_present").metadata
    timer_id = meta["timer_id"]
    run_line(
        ["globus", "timer", "resume", timer_id],
        search_stdout=f"Successfully resumed timer {timer_id}.",
    )


def test_resume_timer_inactive_gare_consent_missing_but_skip_check(run_line):
    meta = load_response_set("cli.timer_resume.inactive_gare.consents_missing").metadata
    timer_id = meta["timer_id"]
    run_line(
        ["globus", "timer", "resume", "--skip-inactive-reason-check", timer_id],
        search_stdout=f"Successfully resumed timer {timer_id}.",
    )


def test_resume_inactive_gare_session_identity(run_line):
    meta = load_response_set(
        "cli.timer_resume.inactive_gare.session_required_identities"
    ).metadata
    timer_id = meta["timer_id"]
    usernames = meta["session_required_identities"]
    run_line(
        ["globus", "timer", "resume", timer_id],
        assert_exit_code=4,
        search_stdout=f"globus session update {' '.join(usernames)}",
    )


def test_resume_inactive_gare_session_identity_but_skip_check(run_line):
    meta = load_response_set(
        "cli.timer_resume.inactive_gare.session_required_identities"
    ).metadata
    timer_id = meta["timer_id"]
    run_line(
        ["globus", "timer", "resume", "--skip-inactive-reason-check", timer_id],
        search_stdout=f"Successfully resumed timer {timer_id}.",
    )


TIMER_ID = str(uuid.uuid1())
TIMER_JSON = {
    "name": "example timer",
    "start": "2022-04-01T19:30:00+00:00",
    "stop_after": None,
    "interval": 864000.0,
    "callback_url": "https://actions.automate.globus.org/transfer/transfer/run",
    "callback_body": {
        "body": {
            "label": "example timer",
            "skip_source_errors": True,
            "sync_level": 3,
            "verify_checksum": True,
            "source_endpoint_id": "aa752cea-8222-5bc8-acd9-555b090c0ccb",
            "destination_endpoint_id": "313ce13e-b597-5858-ae13-29e46fea26e6",
            "transfer_items": [
                {
                    "source_path": "/share/godata/file1.txt",
                    "destination_path": "/~/file1.txt",
                    "recursive": False,
                }
            ],
        }
    },
    "inactive_reason": None,
    "scope": None,
    "job_id": TIMER_ID,
    "status": "loaded",
    "submitted_at": "2022-04-01T19:29:55.942546+00:00",
    "last_ran_at": "2022-04-01T19:30:07.103090+00:00",
    "next_run": "2022-04-11T19:30:00+00:00",
    "n_runs": 1,
    "n_errors": 0,
    "results": {"data": [], "page_next": None},
}


@pytest.fixture(scope="session", autouse=True)
def _register_responses(mock_user_data):
    # Note: this value must match so that the mock login data matches the responses
    user_id = mock_user_data["sub"]
    timer_id = str(uuid.uuid1())
    collection_id = str(uuid.uuid1())
    transfer_scope = globus_sdk.TransferClient.scopes.all
    timers_scope = globus_sdk.TimersClient.scopes.timer
    transfer_ap_scope = _urlscope("actions.globus.org/transfer", "transfer")
    data_access_scope = _urlscope(collection_id, "data_access")
    full_data_access_scope = (
        f"{transfer_ap_scope}[{transfer_scope}[*{data_access_scope}]]"
    )
    required_scope = f"{timers_scope}[{full_data_access_scope}]"

    metadata = {
        "user_id": user_id,
        "timer_id": timer_id,
        "collection_id": collection_id,
        "required_scope": required_scope,
    }

    get_timer_json_consent_gare_body = {
        **TIMER_JSON,
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

    timer_session_identity_gare_body = {
        **TIMER_JSON,
        "status": "inactive",
        "inactive_reason": {
            "cause": "globus_auth_requirements",
            "detail": {
                "code": "AuthorizationParameters",
                "authorization_parameters": {
                    "session_message": "Required identity: foo (GlobusID)",
                    "session_required_identities": ["foo@globusid.org"],
                },
            },
        },
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
        "cli.timer_resume.inactive_gare.consents_missing",
        {
            "get_timer": {
                "service": "timer",
                "path": f"/jobs/{timer_id}",
                "method": "GET",
                "json": get_timer_json_consent_gare_body,
            },
            "resume": {
                "service": "timer",
                "path": f"/jobs/{timer_id}/resume",
                "method": "POST",
                "json": {"message": f"Successfully resumed timer {timer_id}."},
            },
            "consents": {
                "service": "auth",
                "path": f"/v2/api/identities/{user_id}/consents",
                "method": "GET",
                "json": {
                    "consents": [
                        {
                            "scope_name": timers_scope,
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
        "cli.timer_resume.inactive_gare.consents_present",
        {
            "get_timer": {
                "service": "timer",
                "path": f"/jobs/{timer_id}",
                "method": "GET",
                "json": get_timer_json_consent_gare_body,
            },
            "resume": {
                "service": "timer",
                "path": f"/jobs/{timer_id}/resume",
                "method": "POST",
                "json": {"message": f"Successfully resumed timer {timer_id}."},
            },
            "consents": {
                "service": "auth",
                "path": f"/v2/api/identities/{user_id}/consents",
                "method": "GET",
                "json": {
                    "consents": [
                        {
                            "scope_name": timers_scope,
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100],
                            "id": 100,
                            **_dummy_consent_fields,
                        },
                        {
                            "scope_name": transfer_ap_scope,
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100, 101],
                            "id": 101,
                            **_dummy_consent_fields,
                        },
                        {
                            "scope_name": transfer_scope,
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100, 101, 102],
                            "id": 102,
                            **_dummy_consent_fields,
                        },
                        {
                            "scope_name": data_access_scope,
                            "scope": str(uuid.uuid1()),
                            "dependency_path": [100, 101, 102, 103],
                            "id": 103,
                            **_dummy_consent_fields,
                        },
                    ]
                },
            },
        },
        metadata=metadata,
    )
    register_response_set(
        "cli.timer_resume.inactive_gare.session_required_identities",
        {
            "get_timer": {
                "service": "timer",
                "path": f"/jobs/{timer_id}",
                "method": "GET",
                "json": timer_session_identity_gare_body,
            },
            "resume": {
                "service": "timer",
                "path": f"/jobs/{timer_id}/resume",
                "method": "POST",
                "json": {"message": f"Successfully resumed timer {timer_id}."},
            },
        },
        metadata={
            "session_required_identities": ["foo@globusid.org"],
            **metadata,
        },
    )


def _urlscope(m: str, s: str) -> str:
    return f"https://auth.globus.org/scopes/{m}/{s}"
