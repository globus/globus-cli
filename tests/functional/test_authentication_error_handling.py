"""
tests for scenarios in which the credentials in use by the CLI have been
invalidated and are treated as invalid by the services
"""

import uuid

import pytest
from globus_sdk.testing import RegisteredResponse


def test_whoami_unauthorized_error(run_line):
    RegisteredResponse(
        service="auth",
        path="/v2/oauth2/userinfo",
        status=401,
        json={"code": "UNAUTHORIZED", "message": "foo bar"},
    ).add()
    result = run_line("globus whoami", assert_exit_code=1)
    assert "Unable to get user information" in result.stderr


def test_auth_api_call_unauthorized(run_line):
    RegisteredResponse(
        service="auth",
        path="/v2/api/identities",
        status=401,
        json={"code": "UNAUTHORIZED", "message": "foo bar"},
    ).add()
    result = run_line(
        "globus get-identities foo@globusid.org",
        assert_exit_code=1,
    )
    assert "No Authentication provided." in result.stderr


def test_transfer_call_unauthorized(run_line):
    ep_id = str(uuid.uuid1())
    RegisteredResponse(
        service="transfer",
        path=f"/v0.10/operation/endpoint/{ep_id}/ls",
        status=401,
        json={
            "code": "ClientError.AuthenticationFailed",
            "message": "foo bar",
            "request_id": "abc123",
        },
    ).add()
    result = run_line(["globus", "ls", ep_id], assert_exit_code=1)
    assert "No Authentication provided." in result.stderr


@pytest.mark.parametrize(
    # formula for a fake secret: base64.b64encode(os.urandom(32)).decode()
    "client_id, client_secret, id_valid, secret_valid",
    (
        pytest.param(
            str(uuid.UUID(int=0)),
            "Htbj82qnaKmRHBgXprkDHx/eezYDAYGAdlVgGJH3mKU=",
            True,
            True,
            id="valid-shape",
        ),
        pytest.param(
            str(uuid.UUID(int=0))[:-2],
            "Htbj82qnaKmRHBgXprkDHx/eezYDAYGAdlVgGJH3mKU=",
            False,
            True,
            id="invalid-id",
        ),
        pytest.param(
            str(uuid.UUID(int=0)),
            "1",
            True,
            False,
            id="invalid-secret-length",
        ),
        pytest.param(
            str(uuid.UUID(int=0)),
            "Htbj82qnaKmRHBgXprkDHx/eezYDAYGAdlVgGJH3mKU",
            True,
            False,
            id="invalid-secret-padding",
        ),
        pytest.param(
            str(uuid.UUID(int=0))[:-2],
            "YDAYGAdlVgGJH3mKU",
            False,
            False,
            id="both-invalid",
        ),
    ),
)
def test_unauthorized_auth_call_with_client_creds(
    run_line, monkeypatch, client_id, client_secret, id_valid, secret_valid
):
    monkeypatch.setenv("GLOBUS_CLI_CLIENT_ID", client_id)
    monkeypatch.setenv("GLOBUS_CLI_CLIENT_SECRET", client_secret)

    RegisteredResponse(
        service="auth",
        path="/v2/api/identities",
        status=401,
        json={"code": "UNAUTHORIZED", "message": "foo bar"},
    ).add()
    result = run_line(
        "globus get-identities foo@globusid.org",
        assert_exit_code=1,
    )
    assert "MissingLoginError: Invalid Authentication provided." in result.stderr

    bad_client_id_message = (
        "'GLOBUS_CLI_CLIENT_ID' does not appear to be a valid client ID."
    )
    if id_valid:
        assert bad_client_id_message not in result.stderr
    else:
        assert bad_client_id_message in result.stderr

    bad_client_secret_message = (
        "'GLOBUS_CLI_CLIENT_SECRET' does not appear to be a valid client secret."
    )
    if secret_valid:
        assert bad_client_secret_message not in result.stderr
    else:
        assert bad_client_secret_message in result.stderr
