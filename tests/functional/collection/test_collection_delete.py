import pytest
from globus_sdk.testing import load_response_set


# toggle between the (newer) 'gcs' variant and the 'bare' variant
@pytest.fixture(params=("gcs collection", "collection"))
def base_command(request):
    return f"globus {request.param} delete"


def test_guest_collection_delete(run_line, add_gcs_login, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]
    cid = meta["guest_collection_id"]
    add_gcs_login(epid)

    result = run_line(f"{base_command} {cid}")
    assert "success" in result.output


def test_mapped_collection_delete(run_line, add_gcs_login, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]
    cid = meta["mapped_collection_id"]
    add_gcs_login(epid)

    result = run_line(f"{base_command} {cid}")
    assert "success" in result.output


def test_collection_delete_missing_login(run_line, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]
    cid = meta["guest_collection_id"]

    result = run_line(f"{base_command} {cid}", assert_exit_code=4)
    assert "success" not in result.output
    assert "Missing 'manage_collections' consent on an endpoint." in result.stderr
    assert f"  globus login --gcs {epid}" in result.stderr


def test_collection_delete_on_gcsv5_host(run_line, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]

    result = run_line(f"{base_command} {epid}", assert_exit_code=3)
    assert "success" not in result.output
    assert (
        f"Expected {epid} to be a collection ID.\n"
        "Instead, found it was of type 'Globus Connect Server v5 Endpoint'."
    ) in result.stderr
    assert "This operation is not supported on objects of this type." in result.stderr


def test_collection_delete_on_gcp(run_line, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["gcp_endpoint_id"]

    result = run_line(f"{base_command} {epid}", assert_exit_code=3)
    assert "success" not in result.output
    assert (
        f"Expected {epid} to be a collection ID.\n"
        "Instead, found it was of type 'Globus Connect Personal Mapped Collection'."
    ) in result.stderr
    assert (
        "Please run the following command instead:\n\n"
        f"    globus endpoint delete {epid}"
    ) in result.stderr
