import pytest
import responses
from globus_sdk._testing import load_response_set


def get_last_gcs_call(gcs_addr):
    try:
        return next(
            c
            for c in responses.calls[::-1]
            if c.request.url.startswith(f"https://{gcs_addr}")
        )
    except StopIteration:
        return None


def test_collection_list(run_line, add_gcs_login):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]
    add_gcs_login(epid)
    result = run_line(f"globus collection list {epid}")
    collection_names = ["Happy Fun Collection Name 1", "Happy Fun Collection Name 2"]
    for name in collection_names:
        assert name in result.stdout


def test_collection_list_opts(run_line, add_gcs_login):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]
    add_gcs_login(epid)
    cid = meta["mapped_collection_id"]
    run_line(f"globus collection list --mapped-collection-id {cid} {epid}")

    gcs_addr = meta["gcs_hostname"]
    last_call = get_last_gcs_call(gcs_addr)
    assert last_call.request.params["mapped_collection_id"] == cid

    run_line(f"globus collection list --include-private-policies {epid}")
    last_call = get_last_gcs_call(gcs_addr)
    assert last_call.request.params["include"] == "private_policies"


def test_collection_list_on_gcp(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["gcp_endpoint_id"]

    result = run_line(f"globus collection list {epid}", assert_exit_code=3)
    assert "success" not in result.output
    assert (
        f"Expected {epid} to be a Globus Connect Server v5 Endpoint.\n"
        "Instead, found it was of type 'Globus Connect Personal'."
    ) in result.stderr
    assert "This operation is not supported on objects of this type." in result.stderr


def test_collection_list_on_mapped_collection(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["mapped_collection_id"]

    result = run_line(f"globus collection list {epid}", assert_exit_code=3)
    assert "success" not in result.output
    assert (
        f"Expected {epid} to be a Globus Connect Server v5 Endpoint.\n"
        "Instead, found it was of type 'Mapped Collection'."
    ) in result.stderr
    assert "This operation is not supported on objects of this type." in result.stderr


@pytest.mark.parametrize(
    "filter_val",
    [
        "mapped_collections",
        "mapped-collections",
        "MaPpeD-cOLlectiOns",
        "guest-collections",
        "guest_Collections",
        ["Mapped-Collections", "Managed_by-me"],
        ["mapped-collections", "managed-by_me", "created-by-me"],
    ],
)
def test_collection_list_filters(run_line, add_gcs_login, filter_val):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]
    add_gcs_login(epid)
    if not isinstance(filter_val, list):
        filter_val = [filter_val]
    filter_str = " ".join(f"--filter {f}" for f in filter_val)
    run_line(f"globus collection list {filter_str} {epid}")
    filter_params = {v.lower().replace("-", "_") for v in filter_val}

    gcs_addr = meta["gcs_hostname"]
    last_call = get_last_gcs_call(gcs_addr)
    assert set(last_call.request.params["filter"].split(",")) == filter_params
