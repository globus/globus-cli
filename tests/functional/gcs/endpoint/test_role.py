import pytest
from globus_sdk._testing import load_response_set


@pytest.mark.parametrize(
    "principal",
    (
        "foo@globus.org",
        "65eae898-6c3c-45db-99ff-04d7425b8154",
        "65eae898-6c3c-45db-99ff-04d7425b8154 --principal-type identity",
        "urn:globus:auth:identity:65eae898-6c3c-45db-99ff-04d7425b8154",
        "449718d5-32b2-48ba-bd46-e045deab5430 --principal-type group",
        "urn:globus:groups:id:449718d5-32b2-48ba-bd46-e045deab5430",
    ),
)
def test_endpoint_role_create(principal, run_line, add_gcs_login):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(
        f"globus gcs endpoint role create {endpoint_id} activity_manager {principal}"
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


def test_endpoint_role_list(run_line, add_gcs_login):
    meta = load_response_set("cli.endpoint_role_operations").metadata
    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(f"globus gcs endpoint role list {endpoint_id} --all-roles")

    assert role_id in result.stdout


def test_endpoint_role_show(run_line, add_gcs_login):
    meta = load_response_set("cli.endpoint_role_operations").metadata
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
