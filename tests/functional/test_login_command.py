import uuid
from unittest import mock

import globus_sdk
from globus_sdk._testing import load_response_set

from globus_cli.login_manager import LoginManager
from globus_cli.login_manager.auth_flows import (
    _STORE_CONFIG_USERINFO,
    exchange_code_and_store,
)
from tests.conftest import _mock_token_response_data


def test_login_validates_token(run_line, mock_login_token_response):
    # turn off test mode, to allow token validation
    LoginManager._TEST_MODE = False

    with mock.patch("globus_cli.login_manager.manager.internal_auth_client") as m:
        ac = mock.MagicMock(spec=globus_sdk.NativeAppAuthClient)
        m.return_value = ac

        run_line("globus login")

        by_rs = mock_login_token_response.by_resource_server
        a_rt = by_rs["auth.globus.org"]["refresh_token"]
        t_rt = by_rs["transfer.api.globus.org"]["refresh_token"]
        ac.oauth2_validate_token.assert_any_call(a_rt)
        ac.oauth2_validate_token.assert_any_call(t_rt)


class MockToken:
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

    def decode_id_token(self, uuid_value: int = 1):
        return {"sub": str(uuid.UUID(int=uuid_value))}


def test_login_gcs_different_identity(
    monkeypatch,
    run_line,
    mock_remote_session,
    mock_local_server_flow,
    mock_login_token_response,
    test_token_storage,
):
    """
    Test the `exchange_code_and_store` behavior where logging in with a different
    identity is prevented. The user is instructed to logout, which should correctly
    remove the `sub` in config storage (which is what originally raises that error).
    """
    load_response_set("cli.user_info_logout")
    test_token_storage.store_config(
        _STORE_CONFIG_USERINFO, {"sub": str(uuid.UUID(int=0))}
    )
    mock_auth_client = mock.MagicMock(spec=globus_sdk.NativeAppAuthClient)
    mock_auth_client.oauth2_exchange_code_for_tokens = lambda _: MockToken()
    mock_local_server_flow.side_effect = (
        lambda *args, **kwargs: exchange_code_and_store(mock_auth_client, "bogus_code")
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

    monkeypatch.setattr(
        "globus_cli.commands.logout.internal_native_client", lambda: mock_auth_client
    )
    run_line("globus logout --yes")
    assert test_token_storage.read_config(_STORE_CONFIG_USERINFO) is None


def test_login_with_flow(monkeypatch, run_line):
    """Verify that flow ID's are added as resource servers with correct scopes."""

    uuid1 = str(uuid.uuid4())
    scope_name = f'flow_{uuid1.replace("-", "_")}_user'
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
    expected_rs_name_and_scope = (
        uuid1,
        [f"https://auth.globus.org/scopes/{uuid1}/{scope_name}"],
    )
    assert expected_rs_name_and_scope in list(manager.login_requirements)
