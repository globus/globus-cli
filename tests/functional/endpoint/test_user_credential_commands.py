import json
import uuid

import globus_sdk
import responses
from globus_sdk._testing import get_response_set, load_response_set


def test_user_credential_list(add_gcs_login, run_line):
    load_response_set(globus_sdk.GCSClient.get_user_credential_list)
    get_response_set(globus_sdk.AuthClient.get_identities).lookup("default").add()

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    line = f"globus endpoint user-credential list {ep_id}"
    result = run_line(line)

    expected = (
        "ID                                   | Display Name     | Globus Identity                      | Local Username | Invalid\n"  # noqa: E501
        "------------------------------------ | ---------------- | ------------------------------------ | -------------- | -------\n"  # noqa: E501
        "af43d884-64a1-4414-897a-680c32374439 | posix_credential | 948847d4-ffcc-4ae0-ba3a-a4c88d480159 | testuser       | False  \n"  # noqa: E501
        "c96b8f70-1448-46db-89af-292623c93ee4 | s3_credential    | 948847d4-ffcc-4ae0-ba3a-a4c88d480159 | testuser       | False  \n"  # noqa: E501
    )
    assert expected == result.output


def test_user_credential_show(add_gcs_login, run_line):
    cred_meta = load_response_set(globus_sdk.GCSClient.get_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    line = f"globus endpoint user-credential show {ep_id} {cred_id}"
    result = run_line(line)

    expected = (
        "ID:              af43d884-64a1-4414-897a-680c32374439\n"
        "Display Name:    posix_credential\n"
        "Globus Identity: 948847d4-ffcc-4ae0-ba3a-a4c88d480159\n"
        "Local Username:  testuser\n"
        "Connector:       POSIX\n"
        "Invalid:         False\n"
        "Provisioned:     False\n"
        'Policies:        {"DATA_TYPE": "posix_user_credential_policies#1.0.0"}\n'
    )
    assert expected == result.output


def test_user_credential_delete(add_gcs_login, run_line):
    cred_meta = load_response_set(globus_sdk.GCSClient.delete_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    line = f"globus endpoint user-credential delete {ep_id} {cred_id}"
    result = run_line(line)

    expected = f"Deleted User Credential {cred_id}\n"
    assert result.output == expected


def test_user_credential_create_from_json(add_gcs_login, run_line):
    cred_meta = load_response_set(globus_sdk.GCSClient.create_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    json_body = json.dumps({"foo": "bar"})
    line = f"globus endpoint user-credential create from-json {ep_id} '{json_body}'"
    result = run_line(line)

    expected = f"Created User Credential {cred_id}\n"
    assert result.output == expected

    # confirm that the arbitrary dict passed was used
    sent_body = json.loads(responses.calls[-1].request.body)
    assert sent_body == json.loads(json_body)


def test_user_credential_create_from_json_rejects_malformed_data(
    add_gcs_login, run_line
):
    # even though this test should bail out early, setup a full environment for it
    # to run within, ensuring that changes to the order of operations and
    # errors will not break it
    load_response_set(globus_sdk.GCSClient.create_user_credential).metadata

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    json_body = json.dumps(["foo", "bar"])
    line = f"globus endpoint user-credential create from-json {ep_id} '{json_body}'"
    result = run_line(line, assert_exit_code=2)

    assert "User Credential JSON may not contain non-object JSON data" in result.stderr


def test_user_credential_create_posix(add_gcs_login, run_line):
    cred_meta = load_response_set(globus_sdk.GCSClient.create_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    identity_id = meta["identity_id"]
    add_gcs_login(ep_id)

    gateway_id = str(uuid.uuid4())
    globus_identity = "user@globusid.org"
    local_username = "user"

    line = (
        f"globus endpoint user-credential create posix {ep_id} "
        f"{gateway_id} {globus_identity} {local_username}"
    )
    result = run_line(line)

    expected = f"Created User Credential {cred_id}\n"
    assert result.output == expected

    # confirm passed values were used
    sent_body = json.loads(responses.calls[-1].request.body)
    expected_body = dict(
        DATA_TYPE="user_credential#1.0.0",
        storage_gateway_id=gateway_id,
        identity_id=identity_id,
        username=local_username,
    )
    assert sent_body == expected_body


def test_user_credential_create_s3(add_gcs_login, run_line):
    cred_meta = load_response_set(globus_sdk.GCSClient.create_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    identity_id = meta["identity_id"]
    add_gcs_login(ep_id)

    gateway_id = str(uuid.uuid4())
    globus_identity = "user@globusid.org"
    local_username = "user"
    key_id = "foo"
    secret_key = "bar"

    line = (
        f"globus endpoint user-credential create s3 {ep_id} {gateway_id} "
        f"{globus_identity} {local_username} {key_id} {secret_key}"
    )
    result = run_line(line)

    expected = f"Created User Credential {cred_id}\n"
    assert result.output == expected

    # confirm passed values were used
    sent_body = json.loads(responses.calls[-1].request.body)
    expected_body = dict(
        DATA_TYPE="user_credential#1.0.0",
        storage_gateway_id=gateway_id,
        identity_id=identity_id,
        username=local_username,
        policies=dict(
            DATA_TYPE="s3_user_credential_policies#1.0.0",
            s3_key_id=key_id,
            s3_secret_key=secret_key,
        ),
    )
    assert sent_body == expected_body


def test_user_credential_update_from_json(add_gcs_login, run_line):
    cred_meta = load_response_set(globus_sdk.GCSClient.update_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    json_body = json.dumps({"foo": "bar"})
    line = (
        f"globus endpoint user-credential update from-json {ep_id} "
        f"{cred_id} '{json_body}'"
    )
    result = run_line(line)

    expected = f"Updated User Credential {cred_id}\n"
    assert result.output == expected

    # confirm that the arbitrary dict passed was used
    sent_body = json.loads(responses.calls[-1].request.body)
    assert sent_body == json.loads(json_body)


def test_user_credential_update_from_json_rejects_malformed_data(
    add_gcs_login, run_line
):
    # even though this test should bail out early, setup a full environment for it
    # to run within, ensuring that changes to the order of operations and
    # errors will not break it
    cred_meta = load_response_set(globus_sdk.GCSClient.update_user_credential).metadata
    cred_id = cred_meta["id"]

    meta = load_response_set("cli.collection_operations").metadata
    ep_id = meta["endpoint_id"]
    add_gcs_login(ep_id)

    json_body = json.dumps(["foo", "bar"])
    line = (
        f"globus endpoint user-credential update from-json {ep_id} "
        f"{cred_id} '{json_body}'"
    )
    result = run_line(line, assert_exit_code=2)

    assert "User Credential JSON may not contain non-object JSON data" in result.stderr
