import uuid

import pytest
import responses
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize(
    "subscription_id", (str(uuid.UUID(int=101)), "DEFAULT", "null")
)
def test_gcs_endpoint_set_subscription_id(subscription_id, run_line, add_gcs_login):
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    gcs_hostname = meta["gcs_hostname"]
    add_gcs_login(endpoint_id)

    responses.put(
        f"https://{gcs_hostname}/api/endpoint/subscription_id",
        json={
            "DATA_TYPE": "result#1.0.0",
            "code": "success",
            "detail": "success",
            "has_next_page": False,
            "http_response_code": 200,
            "message": f"Updated Endpoint {endpoint_id}",
        },
    )

    result = run_line(
        f"globus gcs endpoint set-subscription-id {endpoint_id} {subscription_id}"
    )

    assert f"Updated Endpoint {endpoint_id}" in result.stdout


def test_gcs_endpoint_set_subscription_id__when_not_subscription_manager(
    run_line, add_gcs_login
):
    meta = load_response_set("cli.collection_operations").metadata
    endpoint_id = meta["endpoint_id"]
    gcs_hostname = meta["gcs_hostname"]
    add_gcs_login(endpoint_id)

    error_message = (
        "Unable to use DEFAULT subscription. Your identity does not manage any"
        "subscriptions"
    )
    responses.put(
        f"https://{gcs_hostname}/api/endpoint/subscription_id",
        status=400,
        json={
            "DATA_TYPE": "result#1.0.0",
            "code": "bad_request",
            "detail": "bad_request",
            "has_next_page": False,
            "http_response_code": 400,
            "message": error_message,
        },
    )

    result = run_line(
        f"globus gcs endpoint set-subscription-id {endpoint_id} DEFAULT",
        assert_exit_code=1,
    )

    assert error_message in result.stderr
