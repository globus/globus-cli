import uuid
from unittest import mock

import pytest
from globus_sdk.token_storage.legacy import SQLiteAdapter


def _add_namespace_to_test_storage(storage, namespace, token_data):
    alt_storage = SQLiteAdapter(":memory:", namespace=namespace)
    try:
        with mock.patch.object(alt_storage, "_connection", storage._connection):
            alt_storage.store(token_data)
    finally:
        alt_storage.close()


@pytest.fixture
def dummy_client_id():
    return str(uuid.uuid1())


@pytest.fixture
def setup_user_profiles(monkeypatch, test_token_storage, mock_login_token_response):
    for profile_name in [
        "production",  # default (no profile name)
        "production/foo-profile",
        "production/bar-profile",
        "production/baz-profile",
        "preview",  # default (no profile name)
        "preview/fizz-profile",
        "preview/buzz-profile",
    ]:
        _add_namespace_to_test_storage(
            test_token_storage, "userprofile/" + profile_name, mock_login_token_response
        )
    # e.g. someone has tinkered with the DB and added other stuff; should be handled and
    # ignored
    _add_namespace_to_test_storage(
        test_token_storage, "BAD_VALUE", mock_login_token_response
    )
    _add_namespace_to_test_storage(
        test_token_storage, "clientprofile/BAD_VALUE", mock_login_token_response
    )


@pytest.fixture
def setup_client_profiles(
    monkeypatch, test_token_storage, mock_login_token_response, dummy_client_id
):
    for env in ("production", "preview"):
        _add_namespace_to_test_storage(
            test_token_storage,
            f"clientprofile/{env}/{dummy_client_id}",
            mock_login_token_response,
        )


@pytest.mark.parametrize("env", ["production", "preview"])
def test_simple_profile_list(setup_user_profiles, run_line, monkeypatch, env):
    monkeypatch.setenv("GLOBUS_SDK_ENVIRONMENT", env)
    result = run_line("globus cli-profile-list")

    for profile_name in ["foo-profile", "bar-profile", "baz-profile"]:
        if env == "production":
            assert profile_name in result.output
        else:
            assert profile_name not in result.output
    for profile_name in ["fizz-profile", "buzz-profile"]:
        if env == "production":
            assert profile_name not in result.output
        else:
            assert profile_name in result.output

    assert "GLOBUS_CLI_CLIENT_ID" not in result.output


def test_profile_list_all(setup_user_profiles, run_line):
    result = run_line("globus cli-profile-list --all")
    for profile_name in [
        "foo-profile",
        "bar-profile",
        "baz-profile",
        "fizz-profile",
        "buzz-profile",
    ]:
        assert profile_name in result.output

    assert "GLOBUS_CLI_CLIENT_ID" not in result.output


def test_profile_list_includes_clients(
    setup_user_profiles, setup_client_profiles, dummy_client_id, run_line
):
    result = run_line("globus cli-profile-list --all")

    for profile_name in [
        "foo-profile",
        "bar-profile",
        "baz-profile",
        "fizz-profile",
        "buzz-profile",
    ]:
        assert profile_name in result.output

    assert "GLOBUS_CLI_CLIENT_ID" in result.output
    assert dummy_client_id in result.output
