import uuid

import pytest
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize(
    "principal_type, add_args",
    (
        ("username", []),
        ("identity_id", []),
        ("identity_id", ["--principal-type", "identity"]),
        ("identity_urn", []),
        ("group_id", ["--principal-type", "group"]),
        ("group_urn", []),
    ),
)
def test_endpoint_role_create(
    run_line, add_gcs_login, get_identities_mocker, principal_type, add_args
):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    user_meta = get_identities_mocker.configure_one(
        id=meta["role_identity_id"]
    ).metadata

    if principal_type == "username":
        principal = user_meta["username"]
    elif principal_type == "identity_id":
        principal = user_meta["id"]
    elif principal_type == "identity_urn":
        principal = f"urn:globus:auth:identity:{user_meta['id']}"
    elif principal_type == "group_id":
        principal = str(uuid.UUID(int=10))
    elif principal_type == "group_urn":
        principal = f"urn:globus:groups:id:{uuid.UUID(int=10)}"
    else:
        raise NotImplementedError(principal_type)

    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(
        [
            "globus",
            "gcs",
            "endpoint",
            "role",
            "create",
            endpoint_id,
            "activity_manager",
            principal,
        ]
        + add_args
    )

    assert role_id in result.stdout


@pytest.mark.parametrize(
    "principal",
    (
        # Email + Group Principal Type
        "foo@globus.org --principal-type group",
        # Identity UUID + Group Principal Type
        (
            "urn:globus:auth:identity:65eae898-6c3c-45db-99ff-04d7425b8154 "
            "--principal-type group"
        ),
        # Group UUID + Identity Principal Type
        (
            "urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430"
            "--principal-type identity"
        ),
    ),
)
def test_endpoint_role_create_with_invalid_principal_input(
    principal, run_line, add_gcs_login
):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    endpoint_id = meta["endpoint_id"]

    add_gcs_login(endpoint_id)

    run_line(
        f"globus gcs endpoint role create {endpoint_id} activity_manager {principal}",
        assert_exit_code=2,
    )


def test_endpoint_role_list(run_line, add_gcs_login, get_identities_mocker):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    get_identities_mocker.configure_one(id=meta["role_identity_id"])
    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(f"globus gcs endpoint role list {endpoint_id} --all-roles")

    assert role_id in result.stdout


def test_endpoint_role_show(run_line, add_gcs_login, get_identities_mocker):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    get_identities_mocker.configure_one(id=meta["role_identity_id"]).metadata

    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(f"globus gcs endpoint role show {endpoint_id} {role_id}")

    assert role_id in result.stdout


def test_endpoint_role_delete(run_line, add_gcs_login):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(f"globus gcs endpoint role delete {endpoint_id} {role_id}")

    assert role_id in result.stdout
