import pytest
from globus_sdk._testing import load_response_set


def test_collection_show(run_line, add_gcs_login):
    meta = load_response_set("cli.collection_operations").metadata
    cid = meta["mapped_collection_id"]
    username = meta["username"]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    run_line(
        f"globus collection show {cid}",
        search_stdout=[
            ("Display Name", "Happy Fun Collection Name"),
            ("Owner", username),
            ("ID", cid),
            ("Collection Type", "mapped"),
            ("Connector", "POSIX"),
        ],
    )


def test_collection_show_private_policies(run_line, add_gcs_login):
    meta = load_response_set("cli.collection_show_private_policies").metadata
    cid = meta["collection_id"]
    username = meta["username"]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    run_line(
        f"globus collection show --include-private-policies {cid}",
        search_stdout=[
            ("Display Name", "Happy Fun Collection Name"),
            ("Owner", username),
            ("ID", cid),
            ("Collection Type", "mapped"),
            ("Connector", "POSIX"),
            ("Root Path", "/"),
            (
                "Sharing Path Restrictions",
                '{"DATA_TYPE": "path_restrictions#1.0.0", "none": ["/"], "read": ["/projects"], "read_write": ["$HOME"]}',  # noqa: E501
            ),
        ],
    )


@pytest.mark.parametrize(
    "epid_key, ep_type",
    [
        ("gcp_endpoint_id", "Globus Connect Personal Mapped Collection"),
        ("endpoint_id", "Globus Connect Server v5 Endpoint"),
    ],
)
def test_collection_show_on_non_collection(run_line, epid_key, ep_type):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta[epid_key]

    result = run_line(f"globus collection show {epid}", assert_exit_code=3)
    assert (
        f"Expected {epid} to be a collection ID.\n"
        f"Instead, found it was of type '{ep_type}'."
    ) in result.stderr
    assert (
        "Please run the following command instead:\n\n"
        f"    globus endpoint show {epid}"
    ) in result.stderr
