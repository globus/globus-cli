import re
import uuid
from unittest.mock import patch

import globus_sdk
import globus_sdk.scopes
import pytest

from globus_cli.login_manager import (
    LoginManager,
    MissingLoginError,
    compute_timer_scope,
)


def mock_get_tokens(resource_server):
    fake_tokens = {
        "a.globus.org": {
            "access_token": "fake_a_access_token",
            "refresh_token": "fake_a_refresh_token",
            "scope": "scopeA1 scopeA2",
        },
        "b.globus.org": {
            "access_token": "fake_b_access_token",
            "refresh_token": "fake_b_refresh_token",
            "scope": "scopeB1 scopeB2",
        },
    }

    return fake_tokens.get(resource_server)


@pytest.fixture(autouse=True)
def patch_static_scopes():
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(
            LoginManager,
            "STATIC_SCOPES",
            {
                "a.globus.org": [
                    "scopeA1",
                    "scopeA2",
                ],
                "b.globus.org": [
                    "scopeB1",
                    "scopeB2",
                ],
            },
        )
        yield mp


def urlfmt_scope(rs: str, name: str) -> str:
    return f"https://auth.globus.org/scopes/{rs}/{name}"


BASE_TIMER_SCOPE = urlfmt_scope("524230d7-ea86-4a52-8312-86065a9e0417", "timer")
TRANSFER_AP_SCOPE = urlfmt_scope("actions.globus.org", "transfer/transfer")


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requires_login_success(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens

    # single server
    @LoginManager.requires_login("a.globus.org")
    def dummy_command(login_manager):
        return True

    assert dummy_command()


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requires_login_multi_server_success(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens

    @LoginManager.requires_login("a.globus.org", "b.globus.org")
    def dummy_command(login_manager):
        return True

    assert dummy_command()


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requires_login_single_server_fail(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens

    @LoginManager.requires_login("c.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for c.globus.org, please run\n\n  globus login\n"
    )


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requiring_new_scope_fails(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens
    LoginManager.STATIC_SCOPES["a.globus.org"].append("scopeA3")

    @LoginManager.requires_login("a.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for a.globus.org, please run\n\n  globus login\n"
    )


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requires_login_fail_two_servers(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens

    @LoginManager.requires_login("c.globus.org", "d.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert re.match(
        "Missing logins for ..globus.org and ..globus.org, "
        "please run\n\n  globus login\n",
        str(ex.value),
    )
    for server in ("c.globus.org", "d.globus.org"):
        assert server in str(ex.value)


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requires_login_fail_multi_server(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens

    @LoginManager.requires_login("c.globus.org", "d.globus.org", "e.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert re.search(
        "Missing logins for ..globus.org, ..globus.org, and ..globus.org", str(ex.value)
    )
    assert "globus login\n" in str(ex.value)
    for server in ("c.globus.org", "d.globus.org", "e.globus.org"):
        assert server in str(ex.value)


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_requires_login_pass_manager(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens

    @LoginManager.requires_login()
    def dummy_command(login_manager):
        assert login_manager.has_login("a.globus.org")
        assert not login_manager.has_login("c.globus.org")

        return True

    assert dummy_command()


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_flow_error_message(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens
    dummy_id = str(uuid.uuid1())

    @LoginManager.requires_login()
    def dummy_command(login_manager):
        login_manager.assert_logins(dummy_id, assume_flow=True)

    with pytest.raises(MissingLoginError) as excinfo:
        dummy_command()

    assert f"globus login --flow {dummy_id}" in str(excinfo.value)


@patch("globus_cli.login_manager.tokenstore.token_storage_adapter")
def test_gcs_error_message(mock_get_adapter):
    mock_get_adapter._instance.get_token_data = mock_get_tokens
    dummy_id = str(uuid.uuid1())

    @LoginManager.requires_login()
    def dummy_command(login_manager):
        login_manager.assert_logins(dummy_id, assume_gcs=True)

    with pytest.raises(MissingLoginError) as excinfo:
        dummy_command()

    assert f"globus login --gcs {dummy_id}" in str(excinfo.value)


def test_client_login_two_requirements(client_login, patch_static_scopes):
    # undo the scope requirements patch
    patch_static_scopes.undo()

    @LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
    def dummy_command(*, login_manager):
        transfer_client = login_manager.get_transfer_client()
        auth_client = login_manager.get_auth_client()

        assert isinstance(
            transfer_client.authorizer, globus_sdk.ClientCredentialsAuthorizer
        )
        assert isinstance(
            auth_client.authorizer, globus_sdk.ClientCredentialsAuthorizer
        )

        return True

    assert dummy_command()


@patch.object(LoginManager, "_get_gcs_info")
def test_client_login_gcs(
    mock_get_gcs_info, client_login, add_gcs_login, patch_static_scopes
):
    patch_static_scopes.undo()

    class fake_endpointish:
        def get_gcs_address(self):
            return "fake_adress"

    gcs_id = "fake_gcs_id"
    mock_get_gcs_info.return_value = gcs_id, fake_endpointish()
    add_gcs_login(gcs_id)

    @LoginManager.requires_login(LoginManager.TRANSFER_RS)
    def dummy_command(*, login_manager, collection_id):
        gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

        assert isinstance(gcs_client.authorizer, globus_sdk.ClientCredentialsAuthorizer)

        return True

    assert dummy_command(collection_id=gcs_id)


def test_compute_timer_scope_no_data_access():
    transfer_scope = globus_sdk.scopes.TransferScopes.all

    computed = str(compute_timer_scope())
    assert computed.startswith(BASE_TIMER_SCOPE)
    assert computed == f"{BASE_TIMER_SCOPE}[{TRANSFER_AP_SCOPE}[{transfer_scope}]]"


def test_compute_timer_scope_one_data_access():
    transfer_scope = globus_sdk.scopes.TransferScopes.all
    foo_scope = urlfmt_scope("foo", "data_access")

    computed = str(compute_timer_scope(data_access_collection_ids=["foo"]))
    assert computed.startswith(BASE_TIMER_SCOPE)
    assert foo_scope in computed
    assert (
        computed
        == f"{BASE_TIMER_SCOPE}[{TRANSFER_AP_SCOPE}[{transfer_scope}[*{foo_scope}]]]"
    )


def test_compute_timer_scope_multiple_data_access():
    transfer_scope = globus_sdk.scopes.TransferScopes.all
    foo_scope = urlfmt_scope("foo", "data_access")
    bar_scope = urlfmt_scope("bar", "data_access")
    baz_scope = urlfmt_scope("baz", "data_access")

    computed = str(
        compute_timer_scope(data_access_collection_ids=["foo", "bar", "baz"])
    )
    assert computed.startswith(BASE_TIMER_SCOPE)
    assert foo_scope in computed
    assert bar_scope in computed
    assert baz_scope in computed
    start_part = f"{BASE_TIMER_SCOPE}[{TRANSFER_AP_SCOPE}[{transfer_scope}["
    end_part = "]]]"
    assert computed == f"{start_part}*{foo_scope} *{bar_scope} *{baz_scope}{end_part}"
