from globus_sdk._testing import RegisteredResponse, load_response_set


def test_successful_gcs_collection_role_creation(
    run_line,
    add_gcs_login,
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

    # mock the responses for the [post] Role API (GCS)
    RegisteredResponse(
        service="gcs",
        path="/roles",
        json={
            "DATA_TYPE": "result#1.1.0",
            "code": "success",
            "data": [
                {
                    "DATA_TYPE": "role#1.0.0",
                    "collection": f"{collection_id}",
                    "id": f"{role_id}",
                    "principal": f"urn:globus:auth:identity:{user_id}",
                    "role": "activity_monitor",
                }
            ],
            "detail": "success",
            "has_next_page": False,
            "http_response_code": 200,
            "message": f"Created new role {role_id}",
        },
    ).add()

    # now test the command and confirm that a successful role creation is reported
    run_line(
        ["globus", "collection", "role", "create", collection_id, role, user_id],
        search_stdout=[
            ("ID", role_id),
        ],
    )
