from globus_sdk.testing import RegisteredResponse, load_response_set


def test_successful_gcs_collection_role_delete(
    run_line,
    add_gcs_login,
):
    # setup data for the collection_id -> endpoint_id lookup
    # and create dummy credentials for the test to run against that GCS
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    collection_id = meta["mapped_collection_id"]
    add_gcs_login(endpoint_id)

    role_id = meta["role_id"]

    # mock the responses for the Get Role API (GCS)
    RegisteredResponse(
        service="gcs",
        path=f"/roles/{role_id}",
        json={
            "DATA_TYPE": "result#1.1.0",
            "code": "success",
            "detail": "success",
            "has_next_page": False,
            "http_response_code": 200,
            "message": f"Deleted role {role_id}",
        },
    ).add()

    # now test the command and confirm that a successful role deletion is reported
    run_line(
        ["globus", "gcs", "collection", "role", "delete", collection_id, role_id],
        search_stdout=[
            "success",
        ],
    )
