import urllib

import pytest
import responses
from globus_sdk.testing import RegisteredResponse

from globus_cli.login_manager import LoginManager


@pytest.fixture(autouse=True)
def _userinfo_matching_logged_in_user(logged_in_user_id, userinfo_mocker):
    userinfo_mocker.configure_unlinked(sub=logged_in_user_id)


@pytest.fixture(autouse=True)
def _delete_client_api_matching_logged_in_client(logged_in_client_id):
    RegisteredResponse(
        service="auth",
        method="DELETE",
        path=f"/v2/api/clients/{logged_in_client_id}",
        json={},
    ).add()


@pytest.fixture(autouse=True)
def _mock_revoke_tokens():
    RegisteredResponse(
        service="auth",
        method="POST",
        path="/v2/oauth2/token/revoke",
        json={"active": False},
    ).add()


@pytest.mark.parametrize("delete_client", [True, False])
def test_logout(delete_client, run_line, mock_login_token_response, test_click_context):
    manager = LoginManager()

    # Collect all of the stored tokens
    stored_tokens = set()
    for token_data in manager.storage.adapter.get_by_resource_server().values():
        stored_tokens.add(token_data["access_token"])
        stored_tokens.add(token_data["refresh_token"])

    assert len(stored_tokens) > 0

    ac_data = manager.storage.read_well_known_config("auth_client_data")
    client_id = ac_data["client_id"]

    additional_args = ["--delete-client"] if delete_client else []
    result = run_line(["globus", "logout", "--yes", *additional_args])

    # One to '/userinfo' and then one to revoke each token
    expected_call_count = 1 + len(stored_tokens)
    if delete_client:
        expected_call_count += 1

    assert len(responses.calls) == expected_call_count

    assert (
        responses.calls[0].request.url == "https://auth.globus.org/v2/oauth2/userinfo"
    )

    revoke_calls = responses.calls[1:]

    if delete_client:
        # Remove the client delete call
        revoke_calls = revoke_calls[1:]

        expected_url = f"https://auth.globus.org/v2/api/clients/{client_id}"
        assert responses.calls[1].request.url == expected_url

    for call in revoke_calls:
        assert call.request.url == "https://auth.globus.org/v2/oauth2/token/revoke"
        assert call.request.method == "POST"
        # Remove each token that's been revoked
        call_args = urllib.parse.parse_qs(call.request.body)
        stored_tokens.remove(call_args["token"][0])

    # Assert they were all revoked
    assert len(stored_tokens) == 0

    assert "You are now successfully logged out" in result.output
    # Make sure the storage was cleared out
    assert manager.storage.read_well_known_config("auth_user_data") is None


@pytest.mark.parametrize("delete_client", [True, False])
def test_logout_with_client_id(
    delete_client, run_line, mock_login_token_response, client_login, test_click_context
):
    manager = LoginManager()

    # Collect all of the stored tokens
    stored_tokens = set()
    for token_data in manager.storage.adapter.get_by_resource_server().values():
        stored_tokens.add(token_data["access_token"])
        stored_tokens.add(token_data["refresh_token"])

    assert len(stored_tokens) > 0

    additional_args = ["--delete-client"] if delete_client else []
    result = run_line(["globus", "logout", "--yes", *additional_args])

    # One to '/userinfo' and then one to revoke each token
    assert len(responses.calls) == 1 + len(stored_tokens)

    assert (
        responses.calls[0].request.url == "https://auth.globus.org/v2/oauth2/userinfo"
    )

    for call in responses.calls[1:]:
        assert call.request.url == "https://auth.globus.org/v2/oauth2/token/revoke"
        assert call.request.method == "POST"
        # Remove each token that's been revoked
        call_args = urllib.parse.parse_qs(call.request.body)
        stored_tokens.remove(call_args["token"][0])

    # Assert they were all revoked
    assert len(stored_tokens) == 0

    assert "Revoking all CLI tokens for" in result.output
    # Make sure the storage was cleared out
    assert manager.storage.read_well_known_config("auth_user_data") is None
