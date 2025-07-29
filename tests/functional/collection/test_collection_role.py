from globus_sdk._testing import load_response_set


def test_collection_role_show(run_line, add_gcs_login):
    meta = load_response_set("cli.collection_role_operations").metadata
    collection_id = meta["collection_id"]
    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(f"globus collection role show {collection_id} {role_id}")

    assert role_id in result.stdout


def test_gcs_collection_role_show_alias(run_line, add_gcs_login):
    meta = load_response_set("cli.collection_role_operations").metadata
    collection_id = meta["collection_id"]
    endpoint_id = meta["endpoint_id"]
    role_id = meta["role_id"]

    add_gcs_login(endpoint_id)

    result = run_line(f"globus gcs collection role show {collection_id} {role_id}")

    assert role_id in result.stdout
