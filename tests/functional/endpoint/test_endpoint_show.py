import pytest
from globus_sdk._testing import load_response_set


@pytest.mark.parametrize("ep_type", ["personal", "share", "server"])
def test_show_works(run_line, ep_type):
    """make sure it doesn't blow up"""
    meta = load_response_set("cli.endpoint_operations").metadata
    if ep_type == "personal":
        epid = meta["gcp_endpoint_id"]
    elif ep_type == "share":
        epid = meta["share_id"]
    else:
        epid = meta["endpoint_id"]

    result = run_line(f"globus endpoint show {epid}")

    assert "Display Name:" in result.output
    assert epid in result.output


def test_show_long_description(run_line):
    meta = load_response_set("cli.endpoint_with_long_description").metadata
    epid = meta["endpoint_id"]

    result = run_line(f"globus endpoint show {epid}")

    assert "Description:" in result.output
    # first few lines are there
    assert "= CLI Changelog\n" in result.output
    assert "== 1.14.0\n" in result.output
    # much later lines should have been truncated out
    assert "== 1.13.0\n" not in result.output


# confirm that this *does not* error:
# showing a GCSv5 host needs to be supported for show (unlike update, delete, etc)
def test_show_on_gcsv5_endpoint(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]

    result = run_line(f"globus endpoint show {epid}")
    assert "Display Name:" in result.output
    assert epid in result.output


def test_show_on_gcsv5_collection(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["mapped_collection_id"]

    result = run_line(f"globus endpoint show {epid}", assert_exit_code=3)
    assert (
        f"Expected {epid} to be an endpoint ID.\n"
        "Instead, found it was of type 'Globus Connect Server v5 Mapped Collection'."
    ) in result.stderr
    assert (
        "Please run the following command instead:\n\n"
        f"    globus collection show {epid}"
    ) in result.stderr


def test_show_on_gcsv5_collection_skip_check(run_line):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["mapped_collection_id"]

    result = run_line(f"globus endpoint show --skip-endpoint-type-check {epid}")
    assert "Display Name:" in result.output
    assert epid in result.output
