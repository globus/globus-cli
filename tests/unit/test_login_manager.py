import re
import sys
import typing as t
import uuid
from unittest import mock

import globus_sdk
import globus_sdk.scopes
import pytest

from globus_cli.login_manager import (
    LoginManager,
    MissingLoginError,
    compute_timer_scope,
)
from globus_cli.login_manager.scopes import (
    CLI_SCOPE_REQUIREMENTS,
    CURRENT_SCOPE_CONTRACT_VERSION,
)
from globus_cli.types import ServiceNameLiteral


@pytest.fixture
def patched_tokenstorage():
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

    def mock_read_config(config_name):
        if config_name == "scope_contract_versions":
            return {
                "a.globus.org": 1,
                "b.globus.org": 1,
            }
        else:
            raise NotImplementedError

    with mock.patch(
        "globus_cli.login_manager.tokenstore.token_storage_adapter._instance"
    ) as mock_adapter:
        mock_adapter.get_token_data = mock_get_tokens
        mock_adapter.read_config = mock_read_config
        yield mock_adapter


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
TRANSFER_AP_SCOPE = urlfmt_scope("actions.globus.org", "transfer/transfer")


def test_requires_login_success(patch_scope_requirements, patched_tokenstorage):
    # single server
    @LoginManager.requires_login("a")
    def dummy_command(login_manager):
        return True

    assert dummy_command()


def test_requires_login_multi_server_success(
    patch_scope_requirements, patched_tokenstorage
):
    @LoginManager.requires_login("a", "b")
    def dummy_command(login_manager):
        return True

    assert dummy_command()


def test_requires_login_single_server_fail(
    patch_scope_requirements, patched_tokenstorage
):
    @LoginManager.requires_login("c.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for c.globus.org, please run:\n\n  globus login\n"
    )


def test_requiring_login_for_multiple_known_servers_renders_nice_error(
    patch_scope_requirements,
):
    @LoginManager.requires_login("a", "b")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing logins for A is for Awesome and B Cool, please run:"
        "\n\n  globus login\n"
    )


def test_requiring_new_scope_fails(patch_scope_requirements, patched_tokenstorage):
    CLI_SCOPE_REQUIREMENTS["a"]["scopes"].append("scopeA3")

    @LoginManager.requires_login("a")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for A is for Awesome, please run:\n\n  globus login\n"
    )


def test_scope_contract_version_bump_forces_login(patch_scope_requirements):
    CLI_SCOPE_REQUIREMENTS["a"]["min_contract_version"] = 2

    @LoginManager.requires_login("a")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert str(ex.value) == (
        "Missing login for A is for Awesome, please run:\n\n  globus login\n"
    )


def test_requires_login_fail_two_servers(
    patch_scope_requirements, patched_tokenstorage
):
    @LoginManager.requires_login("c.globus.org", "d.globus.org")
    def dummy_command(login_manager):
        return True

    with pytest.raises(MissingLoginError) as ex:
        dummy_command()

    assert re.match(
        "Missing logins for ..globus.org and ..globus.org, "
        "please run:\n\n  globus login\n",
        str(ex.value),
    )
    for server in ("c.globus.org", "d.globus.org"):
        assert server in str(ex.value)


def test_requires_login_fail_multi_server(
    patch_scope_requirements, patched_tokenstorage
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


def test_requires_login_pass_manager(patch_scope_requirements, patched_tokenstorage):
    @LoginManager.requires_login()
    def dummy_command(login_manager):
        assert login_manager.has_login("a.globus.org")
        assert not login_manager.has_login("c.globus.org")

        return True

    assert dummy_command()


def test_flow_error_message(patched_tokenstorage):
    dummy_id = str(uuid.uuid1())

    @LoginManager.requires_login()
    def dummy_command(login_manager):
        login_manager.assert_logins(dummy_id, assume_flow=True)

    with pytest.raises(MissingLoginError) as excinfo:
        dummy_command()

    assert f"globus login --flow {dummy_id}" in str(excinfo.value)


def test_gcs_error_message(patched_tokenstorage):
    dummy_id = str(uuid.uuid1())

    @LoginManager.requires_login()
    def dummy_command(login_manager):
        login_manager.assert_logins(dummy_id, assume_gcs=True)

    with pytest.raises(MissingLoginError) as excinfo:
        dummy_command()

    assert f"globus login --gcs {dummy_id}" in str(excinfo.value)


def test_client_login_two_requirements(client_login):
    @LoginManager.requires_login("transfer", "auth")
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


def test_client_login_gcs(client_login, add_gcs_login):
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


@pytest.mark.skipif(sys.version_info < (3, 8), reason="test requires py3.8+")
def test_cli_scope_requirements_exactly_match_service_name_literal():
    scope_requirements_keys = list(CLI_SCOPE_REQUIREMENTS)

    service_name_literal_values = t.get_args(ServiceNameLiteral)
    assert set(service_name_literal_values) == set(scope_requirements_keys)


def test_cli_scope_requirements_min_contract_version_matches_current():
    expect_current_scope_contract_version = max(
        req["min_contract_version"] for req in CLI_SCOPE_REQUIREMENTS.values()
    )
    assert CURRENT_SCOPE_CONTRACT_VERSION == expect_current_scope_contract_version
