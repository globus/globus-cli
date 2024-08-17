import urllib

import pytest
import responses
from globus_sdk._testing import load_response_set

from globus_cli.login_manager import read_well_known_config


@pytest.mark.parametrize("delete_client", [True, False])
def test_logout(delete_client, run_line, test_token_storage, mock_login_token_response):
    load_response_set("cli.logout")

    # Collect all of the stored tokens
    stored_tokens = set()
    for token_data in test_token_storage.get_by_resource_server().values():
        stored_tokens.add(token_data["access_token"])
        stored_tokens.add(token_data["refresh_token"])

    assert len(stored_tokens) > 0

    ac_data = read_well_known_config("auth_client_data", adapter=test_token_storage)
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
    assert read_well_known_config("auth_user_data", adapter=test_token_storage) is None


@pytest.mark.parametrize("delete_client", [True, False])
def test_logout_with_client_id(
    delete_client, run_line, test_token_storage, mock_login_token_response, client_login
):
    load_response_set("cli.logout")

    # Collect all of the stored tokens
    stored_tokens = set()
    for token_data in test_token_storage.get_by_resource_server().values():
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
    assert read_well_known_config("auth_user_data", adapter=test_token_storage) is None
