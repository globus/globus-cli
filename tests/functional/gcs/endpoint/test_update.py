import pytest
from globus_sdk.testing import load_response_set


def test_update_endpoint(run_line, add_gcs_login):
    endpoint_id = load_response_set("cli.endpoint_introspect").metadata["endpoint_id"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    resp = run_line(f"globus gcs endpoint update {endpoint_id} --display-name new-name")

    assert endpoint_id in resp.stdout


@pytest.mark.parametrize("field", ("subscription-id", "gridftp-control-channel-port"))
def test_update_endpoint__nullable_fields_are_nullable(field, run_line, add_gcs_login):
    endpoint_id = load_response_set("cli.endpoint_introspect").metadata["endpoint_id"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    run_line(f"globus gcs endpoint update {endpoint_id} --{field} null")


def test_update_endpoint__network_use_custom_fields_are_required(
    run_line, add_gcs_login
):
    endpoint_id = load_response_set("cli.endpoint_introspect").metadata["endpoint_id"]
    load_response_set("cli.gcs_endpoint_operations")

    add_gcs_login(endpoint_id)

    resp = run_line(
        f"globus gcs endpoint update {endpoint_id} --network-use custom",
        assert_exit_code=2,
    )

    for k in (
        "max-concurrency",
        "max-parallelism",
        "preferred-concurrency",
        "preferred-parallelism",
    ):
        assert k in resp.stderr
