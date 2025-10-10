import pytest
from globus_sdk.testing import load_response_set


# toggle between the (newer) 'gcs' variant and the 'bare' variant
@pytest.fixture(params=("gcs collection", "collection"))
def base_command(request):
    return f"globus {request.param} show"


def test_collection_show(run_line, add_gcs_login, get_identities_mocker, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    user_meta = get_identities_mocker.configure_one(id=meta["identity_id"]).metadata
    cid = meta["mapped_collection_id"]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    run_line(
        f"{base_command} {cid}",
        search_stdout=[
            ("Display Name", "Happy Fun Collection Name"),
            ("Owner", user_meta["username"]),
            ("ID", cid),
            ("Collection Type", "mapped"),
            ("Connector", "POSIX"),
        ],
    )


def test_collection_show_private_policies(
    run_line, add_gcs_login, get_identities_mocker, base_command
):
    meta = load_response_set("cli.collection_show_private_policies").metadata
    user_meta = get_identities_mocker.configure_one(id=meta["user_id"]).metadata
    cid = meta["collection_id"]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    run_line(
        f"{base_command} --include-private-policies {cid}",
        search_stdout=[
            ("Display Name", "Happy Fun Collection Name"),
            ("Owner", user_meta["username"]),
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
def test_collection_show_on_non_collection(run_line, base_command, epid_key, ep_type):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta[epid_key]

    result = run_line(f"{base_command} {epid}", assert_exit_code=3)
    assert (
        f"Expected {epid} to be a collection ID.\n"
        f"Instead, found it was of type '{ep_type}'."
    ) in result.stderr
    assert (
        "Please run the following command instead:\n\n"
        f"    globus endpoint show {epid}"
    ) in result.stderr
