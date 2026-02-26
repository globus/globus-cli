from globus_sdk.testing import load_response_set


def test_successful_gcs_collection_role_creation(
    run_line,
    add_gcs_login,
    get_identities_mocker,
):
    # setup data for the collection_id -> endpoint_id lookup
    # and create dummy credentials for the test to run against that GCS
    meta = load_response_set("cli.collection_operations").metadata

    collection_id = meta["mapped_collection_id"]
    endpoint_id = meta["endpoint_id"]
    role = meta["role"]
    role_id = meta["role_id"]
    user_id = meta["identity_id"]
    add_gcs_login(endpoint_id)

    role = "activity_monitor"

    # Mock the Get Identities API (Auth)
    # so that CLI output rendering can show a username
    user_meta = get_identities_mocker.configure_one(id=user_id).metadata
    username = user_meta["username"]

    # now test the command and confirm that a successful role creation is reported
    run_line(
        ["globus", "gcs", "collection", "role", "create", collection_id, role, user_id],
        search_stdout=[
            ("ID", role_id),
            ("Role", role),
            ("Principal", username),
        ],
    )
