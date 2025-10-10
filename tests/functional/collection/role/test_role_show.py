import uuid

from globus_sdk.testing import RegisteredResponse, load_response_set


def test_successful_gcs_collection_role_show(
    run_line,
    add_gcs_login,
    get_identities_mocker,
):
    # setup data for the collection_id -> endpoint_id lookup
    # and create dummy credentials for the test to run against that GCS
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    collection_id = meta["mapped_collection_id"]
    add_gcs_login(endpoint_id)

    role_id = str(uuid.UUID(int=1))
    user_id = str(uuid.UUID(int=2))

    # mock the responses for the Get Role API (GCS)
    RegisteredResponse(
        service="gcs",
        path=f"/roles/{role_id}",
        json={
            "DATA_TYPE": "role#1.0.0",
            "collection": collection_id,
            "id": role_id,
            "principal": f"urn:globus:auth:identity:{user_id}",
            "role": "administrator",
        },
    ).add()

    # Mock the Get Identities API (Auth)
    # so that CLI output rendering can show a username
    user_meta = get_identities_mocker.configure_one(id=user_id).metadata
    username = user_meta["username"]

    # now test the command and confirm that output shows the role name and the
    # username
    run_line(
        ["globus", "gcs", "collection", "role", "show", collection_id, role_id],
        search_stdout=[
            ("Role", "administrator"),
            ("Principal", username),
        ],
    )
