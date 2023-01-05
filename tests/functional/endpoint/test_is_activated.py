import uuid

from globus_sdk._testing import RegisteredResponse, load_response


def test_no_activation_required(run_line):
    epid = str(uuid.uuid4())
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/endpoint/{epid}/activation_requirements",
            json={
                "expires_in": -1,
                "activated": True,
                "auto_activation_supported": True,
                "oauth_server": None,
                "DATA": [],
            },
        )
    )
    result = run_line(f"globus endpoint is-activated {epid}")
    assert f"'{epid}' does not require activation" in result.output


def test_currently_active(run_line):
    epid = str(uuid.uuid4())
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/endpoint/{epid}/activation_requirements",
            json={
                "expires_in": 3600,
                "activated": True,
                "auto_activation_supported": False,
                "oauth_server": None,
                "DATA": [],
            },
        )
    )
    result = run_line(f"globus endpoint is-activated {epid}")
    assert f"'{epid}' is activated" in result.output


def test_not_currently_active(run_line):
    epid = str(uuid.uuid4())
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/endpoint/{epid}/activation_requirements",
            json={
                "expires_in": 0,
                "activated": False,
                "auto_activation_supported": False,
                "oauth_server": None,
                "DATA": [],
            },
        )
    )
    result = run_line(f"globus endpoint is-activated {epid}", assert_exit_code=1)
    assert f"'{epid}' is not activated" in result.output


def test_active_until_deadline(run_line):
    epid = str(uuid.uuid4())
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/endpoint/{epid}/activation_requirements",
            json={
                "expires_in": 3600,
                "activated": True,
                "auto_activation_supported": False,
                "oauth_server": None,
                "DATA": [],
            },
        )
    )
    result = run_line(f"globus endpoint is-activated {epid} --until 60")
    assert f"'{epid}' will be active for at least 60 seconds" in result.output


def test_not_active_until_deadline(run_line):
    epid = str(uuid.uuid4())
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/endpoint/{epid}/activation_requirements",
            json={
                "expires_in": 600,
                "activated": True,
                "auto_activation_supported": False,
                "oauth_server": None,
                "DATA": [],
            },
        )
    )
    result = run_line(
        f"globus endpoint is-activated {epid} --until 3600", assert_exit_code=1
    )
    assert (
        f"'{epid}' is not activated or will expire within 3600 seconds" in result.output
    )
