import uuid
from unittest import mock

import globus_sdk
import pytest
from globus_sdk.testing import RegisteredResponse

from globus_cli.login_manager import LoginManager
from globus_cli.login_manager.auth_flows import exchange_code_and_store
from tests.conftest import _mock_token_response_data


def test_login_validates_token(
    run_line, mock_login_token_response, disable_login_manager_validate_token
):
    # undo the validate_token disabling patch which is done for most tests
    disable_login_manager_validate_token.undo()

    ac = mock.MagicMock(spec=globus_sdk.ConfidentialAppAuthClient)
    with mock.patch(
        "globus_cli.login_manager.storage.CLIStorage.cli_confidential_client", ac
    ):
        run_line("globus login")

        by_rs = mock_login_token_response.by_resource_server
        a_rt = by_rs["auth.globus.org"]["refresh_token"]
        t_rt = by_rs["transfer.api.globus.org"]["refresh_token"]
        ac.post.assert_any_call(
            "/v2/oauth2/token/validate", data={"token": a_rt}, encoding="form"
        )
        ac.post.assert_any_call(
            "/v2/oauth2/token/validate", data={"token": t_rt}, encoding="form"
        )


class MockToken:
    def __init__(self, uuid_value: int = 1) -> None:
        self._uuid_value = uuid_value

    by_resource_server = {
        "auth.globus.org": _mock_token_response_data(
            "auth.globus.org",
            "openid profile email "
            "urn:globus:auth:scope:auth.globus.org:view_identity_set",
        ),
        "transfer.api.globus.org": _mock_token_response_data(
            "transfer.api.globus.org",
            "urn:globus:auth:scope:transfer.api.globus.org:all",
        ),
    }

    def decode_id_token(self, *args, **kwargs):
        return {"sub": str(uuid.UUID(int=self._uuid_value))}


def test_login_gcs_different_identity(
    monkeypatch,
    run_line,
    logged_in_client_id,
    userinfo_mocker,
    mock_remote_session,
    mock_local_server_flow,
    mock_login_token_response,
    test_click_context,
):
    """
    Test the `exchange_code_and_store` behavior where logging in with a different
    identity is prevented. The user is instructed to logout, which should correctly
    remove the `sub` in config storage (which is what originally raises that error).
    """
    userinfo_mocker.configure_unlinked(sub=str(uuid.UUID(int=10)))
    manager = LoginManager()
    manager.storage.store_well_known_config(
        "auth_user_data", {"sub": str(uuid.UUID(int=0))}
    )
    mock_auth_client = mock.MagicMock(spec=globus_sdk.NativeAppAuthClient)
    mock_auth_client.oauth2_exchange_code_for_tokens = lambda _: MockToken()
    mock_local_server_flow.side_effect = (
        lambda *args, **kwargs: exchange_code_and_store(
            manager.storage, mock_auth_client, "bogus_code"
        )
    )
    mock_remote_session.return_value = False
    result = run_line(f"globus login --gcs {uuid.UUID(int=0)}", assert_exit_code=1)
    assert "Authorization failed" in result.stderr
    mock_auth_client.oauth2_revoke_token.assert_has_calls(
        [
            mock.call(t)
            for v in MockToken.by_resource_server.values()
            for t in (v["access_token"], v["refresh_token"])
        ],
        any_order=True,
    )

    # setup network mocks to ensure that 'logout' can run
    RegisteredResponse(
        service="auth",
        method="DELETE",
        path=f"/v2/api/clients/{logged_in_client_id}",
        json={},
    ).add()
    RegisteredResponse(
        service="auth",
        method="POST",
        path="/v2/oauth2/token/revoke",
        json={"active": False},
    ).add()
    monkeypatch.setattr(
        "globus_cli.login_manager.storage.CLIStorage.cli_confidential_client",
        mock_auth_client,
    )
    run_line("globus logout --yes")
    assert manager.storage.read_well_known_config("auth_user_data") is None


def test_login_with_flow(monkeypatch, run_line):
    """Verify that flow ID's are added as resource servers with correct scopes."""

    uuid1 = str(uuid.uuid4())
    manager: LoginManager | None = None

    def intercept_run_login_flow(self, *_, **__):
        # Capture the LoginManager instance so its scopes can be reviewed.
        nonlocal manager
        manager = self

    monkeypatch.setattr(LoginManager, "run_login_flow", intercept_run_login_flow)

    # Run a login flow with a specific flow ID.
    run_line(f"globus login --flow {uuid1}")

    # Verify that intercept_run_login_flow() captured the LoginManager instance.
    assert manager is not None

    # Verify that the expected resource server and scope were added as requirements.
    # This can only happen if the `--flow <uuid>` CLI argument is working correctly.
    client = globus_sdk.SpecificFlowClient(uuid1)
    expected_rs_name_and_scope = (client.scopes.resource_server, [client.scopes.user])
    assert expected_rs_name_and_scope in list(manager.login_requirements)


@pytest.mark.parametrize("quiet_mode", (True, False))
def test_login_quiet_mode_suppresses_output(run_line, quiet_mode):
    result = run_line(["globus", "login"] + (["--quiet"] if quiet_mode else []))
    if quiet_mode:
        assert result.output == ""
    else:
        assert "You are already logged in!" in result.output
