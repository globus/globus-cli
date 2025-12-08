import datetime
import re
import typing as t
import uuid
from unittest import mock

import click
import globus_sdk
import globus_sdk.scopes
import jwt
import pytest

from globus_cli.login_manager import (
    LoginManager,
    MissingLoginError,
    compute_timer_scope,
)
from globus_cli.login_manager.auth_flows import exchange_code_and_store
from globus_cli.login_manager.context import LoginContext
from globus_cli.login_manager.scopes import (
    CLI_SCOPE_REQUIREMENTS,
    CURRENT_SCOPE_CONTRACT_VERSION,
)
from globus_cli.types import ServiceNameLiteral


@pytest.fixture
def patched_tokenstorage(test_token_storage):
    def fake_get_tokens(resource_server):
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

    def fake_read_config(self, config_name):
        if config_name == "scope_contract_versions":
            return {
                "a.globus.org": 1,
                "b.globus.org": 1,
            }
        else:
            raise NotImplementedError

    test_token_storage.get_token_data = mock.Mock()
    test_token_storage.get_token_data.side_effect = fake_get_tokens

    with mock.patch(
        "globus_cli.login_manager.storage.CLIStorage.read_well_known_config",
        fake_read_config,
    ):
        yield


@pytest.fixture
def patch_scope_requirements():
    with pytest.MonkeyPatch().context() as mp:
        prior_keys = list(CLI_SCOPE_REQUIREMENTS)
        # clear prior contents
        for k in prior_keys:
            mp.delitem(CLI_SCOPE_REQUIREMENTS, k)

        mp.setitem(
            CLI_SCOPE_REQUIREMENTS,
            "a",
            {
                "min_contract_version": 0,
                "resource_server": "a.globus.org",
                "nice_server_name": "A is for Awesome",
                "scopes": [
                    "scopeA1",
                    "scopeA2",
                ],
            },
        )
        mp.setitem(
            CLI_SCOPE_REQUIREMENTS,
            "b",
            {
                "min_contract_version": 0,
                "resource_server": "b.globus.org",
                "nice_server_name": "B Cool",
                "scopes": [
                    "scopeB1",
                    "scopeB2",
                ],
            },
        )
        yield mp


def urlfmt_scope(rs: str, name: str) -> str:
    return f"https://auth.globus.org/scopes/{rs}/{name}"


BASE_TIMER_SCOPE = urlfmt_scope("524230d7-ea86-4a52-8312-86065a9e0417", "timer")


def test_requires_login_success(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
    # single server
    @LoginManager.requires_login("a")
    def dummy_command(login_manager):
        return True

    assert dummy_command()


def test_requires_login_multi_server_success(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
    @LoginManager.requires_login("a", "b")
    def dummy_command(login_manager):
        return True

    assert dummy_command()


def test_requires_login_single_server_fail(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
    @LoginManager.requires_login("c.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for c.globus.org.\nPlease run:\n\n  globus login\n"
    )


def test_requiring_login_for_multiple_known_servers_renders_nice_error(
    patch_scope_requirements,
    test_click_context,
):
    @LoginManager.requires_login("a", "b")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing logins for A is for Awesome and B Cool.\nPlease run:"
        "\n\n  globus login\n"
    )


def test_requiring_new_scope_fails(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
    CLI_SCOPE_REQUIREMENTS["a"]["scopes"].append("scopeA3")

    @LoginManager.requires_login("a")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for A is for Awesome.\nPlease run:\n\n  globus login\n"
    )


def test_scope_contract_version_bump_forces_login(
    patch_scope_requirements, test_click_context
):
    CLI_SCOPE_REQUIREMENTS["a"]["min_contract_version"] = 2

    @LoginManager.requires_login("a")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for A is for Awesome.\nPlease run:\n\n  globus login\n"
    )


def test_requires_login_fail_two_servers(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
    @LoginManager.requires_login("c.globus.org", "d.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert re.match(
        "Missing logins for ..globus.org and ..globus.org.\n"
        "Please run:\n\n  globus login\n",
        str(ex.value),
    )
    for server in ("c.globus.org", "d.globus.org"):
        assert server in str(ex.value)


def test_requires_login_fail_multi_server(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
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


def test_requires_login_pass_manager(
    patch_scope_requirements, patched_tokenstorage, test_click_context
):
    @LoginManager.requires_login()
    def dummy_command(login_manager):
        assert login_manager.has_login("a.globus.org")
        assert not login_manager.has_login("c.globus.org")

        return True

    assert dummy_command()


def test_login_manager_respects_context_error_message(
    patched_tokenstorage, test_click_context
):
    dummy_id = str(uuid.uuid1())

    @LoginManager.requires_login()
    def dummy_command(login_manager):
        login_context = LoginContext(
            login_command="globus try-again",
            error_message="Well that went pretty poorly!",
        )
        login_manager.assert_logins(dummy_id, login_context=login_context)

    with pytest.raises(MissingLoginError) as excinfo:
        dummy_command()

    expected = "Well that went pretty poorly!\nPlease run:\n\n  globus try-again\n"
    assert expected == str(excinfo.value)


def test_client_login_two_requirements(client_login, test_click_context):
    @LoginManager.requires_login("auth", "transfer")
    def dummy_command(login_manager):
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


def test_client_login_gcs(client_login, add_gcs_login, test_click_context):
    with mock.patch.object(LoginManager, "_get_gcs_info") as mock_get_gcs_info:

        class fake_endpointish:
            def get_gcs_address(self):
                return "fake_adress"

        gcs_id = "fake_gcs_id"
        mock_get_gcs_info.return_value = gcs_id, fake_endpointish()
        add_gcs_login(gcs_id)

        @LoginManager.requires_login("transfer")
        def dummy_command(login_manager, *, collection_id):
            gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

            assert isinstance(
                gcs_client.authorizer, globus_sdk.ClientCredentialsAuthorizer
            )

            return True

        assert dummy_command(collection_id=gcs_id)


def test_compute_timer_scope_no_data_access():
    transfer_scope = globus_sdk.scopes.TransferScopes.all

    computed = str(compute_timer_scope())
    assert computed.startswith(BASE_TIMER_SCOPE)
    assert computed == f"{BASE_TIMER_SCOPE}[{transfer_scope}]"


def test_compute_timer_scope_one_data_access():
    transfer_scope = globus_sdk.scopes.TransferScopes.all
    foo_scope = urlfmt_scope("foo", "data_access")

    computed = str(compute_timer_scope(data_access_collection_ids=["foo"]))
    assert computed.startswith(BASE_TIMER_SCOPE)
    assert foo_scope in computed
    assert computed == f"{BASE_TIMER_SCOPE}[{transfer_scope}[*{foo_scope}]]"


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
    start_part = f"{BASE_TIMER_SCOPE}[{transfer_scope}["
    end_part = "]]"
    assert computed == f"{start_part}*{foo_scope} *{bar_scope} *{baz_scope}{end_part}"


def test_cli_scope_requirements_exactly_match_service_name_literal():
    scope_requirements_keys = list(CLI_SCOPE_REQUIREMENTS)

    service_name_literal_values = t.get_args(ServiceNameLiteral)
    assert set(service_name_literal_values) == set(scope_requirements_keys)


def test_cli_scope_requirements_min_contract_version_matches_current():
    expect_current_scope_contract_version = max(
        req["min_contract_version"] for req in CLI_SCOPE_REQUIREMENTS.values()
    )
    assert CURRENT_SCOPE_CONTRACT_VERSION == expect_current_scope_contract_version


def test_immature_signature_during_jwt_decode_emits_clock_skew_notice(
    capsys,
    monkeypatch,
    test_click_context,
):
    """
    Test the `exchange_code_and_store` behavior when the id_token decoding fails
    due to clock skew.

    This should result in a clear error emitted to stderr.
    """
    manager = LoginManager()

    mock_token_response = mock.Mock()
    mock_token_response.decode_id_token = mock.Mock(
        side_effect=jwt.exceptions.ImmatureSignatureError("test")
    )
    mock_token_response.headers = {
        "Date": (
            datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(seconds=300)
        ).strftime("%a, %d %b %Y %H:%M:%S %Z")
    }

    mock_auth_client = mock.MagicMock(spec=globus_sdk.NativeAppAuthClient)
    mock_auth_client.oauth2_exchange_code_for_tokens = mock.Mock(
        return_value=mock_token_response
    )

    with pytest.raises(jwt.exceptions.ImmatureSignatureError):
        exchange_code_and_store(manager.storage, mock_auth_client, "bogus_code")

    stderr = capsys.readouterr().err
    assert "out of sync with the local clock" in stderr
    assert "This may indicate a clock skew problem." in stderr


@pytest.mark.parametrize("date_parse_fail_modality", ("missing", "invalid", "emptystr"))
def test_immature_signature_during_jwt_decode_skips_notice_if_date_cannot_parse(
    capsys,
    monkeypatch,
    test_token_storage,
    date_parse_fail_modality,
):
    """
    Test the `exchange_code_and_store` behavior when the id_token decoding fails
    due to clock skew.

    This should result in a clear error emitted to stderr.
    """
    manager = LoginManager()

    mock_token_response = mock.Mock()
    mock_token_response.decode_id_token = mock.Mock(
        side_effect=jwt.exceptions.ImmatureSignatureError("test")
    )
    if date_parse_fail_modality == "missing":
        mock_token_response.headers = {}
    elif date_parse_fail_modality == "invalid":
        mock_token_response.headers = {"Date": "1970-01-01 00:00:00 GMT"}
    elif date_parse_fail_modality == "emptystr":
        mock_token_response.headers = {"Date": ""}
    else:
        raise NotImplementedError

    mock_auth_client = mock.MagicMock(spec=globus_sdk.NativeAppAuthClient)
    mock_auth_client.oauth2_exchange_code_for_tokens = mock.Mock(
        return_value=mock_token_response
    )

    with pytest.raises(jwt.exceptions.ImmatureSignatureError):
        exchange_code_and_store(manager.storage, mock_auth_client, "bogus_code")

    stderr = capsys.readouterr().err
    assert "This may indicate a clock skew problem." not in stderr


def test_login_manager_closes_created_clients_after_context_exit(test_token_storage):
    from globus_cli.commands import main

    def add_close_spy(client):
        real_close = client.close
        spy = mock.Mock(side_effect=real_close)
        client.close = spy
        return spy

    with click.Context(main):
        spy1, spy2 = None, None

        @LoginManager.requires_login("auth", "transfer")
        def dummy_command(login_manager):
            transfer_client = login_manager.get_transfer_client()
            auth_client = login_manager.get_auth_client()

            nonlocal spy1, spy2
            spy1 = add_close_spy(transfer_client)
            spy2 = add_close_spy(auth_client)
            return True

        assert dummy_command()

        spy1.assert_not_called()
        spy2.assert_not_called()

    spy1.assert_called_once()
    spy2.assert_called_once()
