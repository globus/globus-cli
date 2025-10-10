import uuid
from copy import copy

import pytest
import requests
import responses
from globus_sdk.testing import load_response_set
from globus_sdk.config import get_service_url

from globus_cli.endpointish import EntityType


def test_guest_collection_create(run_line, get_identities_mocker, add_gcs_login):
    meta = load_response_set("cli.collection_operations").metadata
    get_identities_mocker.configure_one(id=meta["identity_id"])
    endpoint_id = meta["endpoint_id"]
    mapped_collection_id = meta["mapped_collection_id"]
    guest_collection_id = meta["guest_collection_id"]
    display_name = meta["guest_display_name"]
    add_gcs_login(endpoint_id)

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}")

    assert display_name in result.output
    assert guest_collection_id in result.output
    assert "guest" in result.output


def test_guest_collection_create__when_missing_login(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=4)

    assert "MissingLoginError" in result.stderr
    assert f"globus login --gcs {endpoint_id}:{mapped_collection_id}" in result.stderr


def test_guest_collection_create__when_missing_consent(
    run_line, add_gcs_login, mock_user_data
):
    """
    Creating guest collections may require a data_access scope consent (based on whether
      the mapped collection is HA or not).

    This test simulates a situation where
      1. The data_access scope is required
      2. The user has valid token already for the `collection_manager` scope but hasn't
         consented to `collection_manager[data_access]`
    """
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]
    add_gcs_login(endpoint_id)

    # Remove any `data_access` consents from the consents response
    consent_route = (
        f"{get_service_url('auth')}v2/api/identities/{mock_user_data['sub']}/consents"
    )
    registered_consents = requests.get(consent_route).json()["consents"]
    responses.replace(
        "GET",
        consent_route,
        json={
            "consents": [
                consent
                for consent in registered_consents
                if not consent["scope_name"].endswith("data_access")
            ]
        },
    )

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=4)

    assert "MissingLoginError" in result.stderr
    assert f"globus login --gcs {endpoint_id}:{mapped_collection_id}" in result.stderr


@pytest.mark.parametrize("explicit_local_username", (True, False))
def test_guest_collection_create__when_multiple_matching_user_credentials(
    explicit_local_username, run_line, add_gcs_login
):
    """
    The requisite API call for command test requires an explicit `user_credential_id`.
    The CLI supports this but additionally tries to implicitly supply one if omitted
      from existing user credentials.

    This test verifies that the CLI will error with a helpful message if multiple
      valid user credentials are discovered when `--user-credential-id` is omitted.
    """
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]
    local_username = meta["local_username"]
    gcs_hostname = meta["gcs_hostname"]
    add_gcs_login(endpoint_id)

    # Duplicate the single registered user credential
    user_credentials_route = f"https://{gcs_hostname}/api/user_credentials"
    registered_credential_resp = requests.get(user_credentials_route).json()
    registered_credential_copy = copy(registered_credential_resp["data"][0])
    registered_credential_copy["id"] = str(uuid.uuid4())
    registered_credential_copy["display_name"] = "backup"

    registered_credential_resp["data"].append(registered_credential_copy)
    responses.replace("GET", user_credentials_route, json=registered_credential_resp)

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    if explicit_local_username:
        params += f" --local-username {local_username}"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=1)

    assert "More than one gcs user credential valid for creation." in result.stderr
    suggestion = "Please try again supplying "
    if explicit_local_username:
        suggestion += "either --local-username or "
    suggestion += "--user-credential-id."


def test_guest_collection_create__when_no_matching_user_credentials(
    run_line, add_gcs_login
):
    """
    The requisite API call for command test requires an explicit `user_credential_id`.
    The CLI supports this but additionally tries to implicitly supply one if omitted
      from existing user credentials.

    This test verifies that the CLI will error with a helpful message if no valid
      user credentials are discovered when `--user-credential-id` is omitted.
    """
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]
    gcs_hostname = meta["gcs_hostname"]
    add_gcs_login(endpoint_id)

    # Remove any registered user credentials
    user_credentials_route = f"https://{gcs_hostname}/api/user_credentials"
    registered_credential_resp = requests.get(user_credentials_route).json()
    registered_credential_resp["data"] = []
    responses.replace("GET", user_credentials_route, json=registered_credential_resp)

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=1)

    assert "No valid gcs user credentials discovered." in result.stderr
    assert endpoint_id in result.stderr
    assert "globus endpoint user-credential create" in result.stderr


@pytest.mark.parametrize(
    "collection_type", [e for e in EntityType if e is not EntityType.GCSV5_MAPPED]
)
def test_guest_collection_create__when_mapped_collection_type_is_unsupported(
    collection_type,
    run_line,
):
    meta = load_response_set("cli.collection_operations").metadata
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]

    get_endpoint_route = (
        f"{get_service_url('transfer')}v0.10/endpoint/{mapped_collection_id}"
    )
    get_endpoint_resp = requests.get(get_endpoint_route).json()
    get_endpoint_resp["entity_type"] = collection_type.value
    responses.replace("GET", get_endpoint_route, json=get_endpoint_resp)

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=3)

    assert f"Expected {mapped_collection_id} to be a" in result.stderr
    msg = f"Instead, found it was of type '{EntityType.nice_name(collection_type)}'."
    assert msg in result.stderr


def test_guest_collection_create__when_session_times_out_against_ha_mapped_collection(
    run_line,
    mock_user_data,
    add_gcs_login,
):
    meta = load_response_set("cli.collection_operations").metadata
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]
    gcs_hostname = meta["gcs_hostname"]
    endpoint_id = meta["endpoint_id"]
    add_gcs_login(endpoint_id)

    create_guest_collection_route = f"https://{gcs_hostname}/api/collections"
    responses.replace(
        "POST",
        create_guest_collection_route,
        status=403,
        json={
            "DATA_TYPE": "result#1.0.0",
            "code": "permission_denied",
            "detail": {
                "DATA_TYPE": "authentication_timeout#1.1.0",
                "high_assurance": True,
                "identities": [mock_user_data["sub"]],
                "require_mfa": False,
            },
            "has_next_page": False,
            "http_response_code": 403,
            "message": (
                "You must reauthenticate one of your identities (sirosen@globus.org) "
                "in order to access this resource"
            ),
        },
    )

    get_endpoint_route = (
        f"{get_service_url('transfer')}v0.10/endpoint/{mapped_collection_id}"
    )
    get_endpoint_resp = requests.get(get_endpoint_route).json()
    get_endpoint_resp["high_assurance"] = True
    responses.replace("GET", get_endpoint_route, json=get_endpoint_resp)

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=4)

    assert "Session timeout detected; Re-authentication required." in result.stderr
    assert f"globus login --gcs {endpoint_id} --force" in result.stderr


def test_guest_collection_create__when_gcs_emits_unrecognized_error(
    run_line,
    mock_user_data,
    add_gcs_login,
):
    meta = load_response_set("cli.collection_operations").metadata
    mapped_collection_id = meta["mapped_collection_id"]
    display_name = meta["guest_display_name"]
    gcs_hostname = meta["gcs_hostname"]
    endpoint_id = meta["endpoint_id"]
    add_gcs_login(endpoint_id)

    create_guest_collection_route = f"https://{gcs_hostname}/api/collections"
    responses.replace(
        "POST",
        create_guest_collection_route,
        status=403,
        json={
            "DATA_TYPE": "result#1.0.0",
            "code": "permission_denied",
            "detail": "oh noez!",
            "has_next_page": False,
            "http_response_code": 403,
            "message": "Oh noez! You must authenticate much better!",
        },
    )

    get_endpoint_route = (
        f"{get_service_url('transfer')}v0.10/endpoint/{mapped_collection_id}"
    )
    get_endpoint_resp = requests.get(get_endpoint_route).json()
    get_endpoint_resp["high_assurance"] = True
    responses.replace("GET", get_endpoint_route, json=get_endpoint_resp)

    params = f"{mapped_collection_id} /home/ '{display_name}'"
    result = run_line(f"globus collection create guest {params}", assert_exit_code=1)

    assert "Session timeout detected" not in result.stderr
    assert "Oh noez! You must authenticate much better!" in result.stderr
