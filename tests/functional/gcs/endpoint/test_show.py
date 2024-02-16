from globus_sdk._testing import load_response_set


def test_endpoint_show(run_line, add_gcs_login):
    endpoint_id = load_response_set("cli.endpoint_introspect").metadata["endpoint_id"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    resp = run_line(f"globus gcs endpoint show {endpoint_id}")

    assert endpoint_id in resp.stdout
