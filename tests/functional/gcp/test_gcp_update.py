import json
import uuid

import pytest
from globus_sdk.testing import (
    get_last_request,
    load_response_set,
    register_response_set,
)


@pytest.fixture(scope="session", autouse=True)
def _update_mapped_responses():
    ep_id = str(uuid.uuid1())
    register_response_set(
        "gcp_update_mapped",
        {
            "default": {
                "service": "transfer",
                "path": f"/endpoint/{ep_id}",
                "method": "PUT",
                "json": {
                    "DATA_TYPE": "endpoint_update_result",
                    "code": "Updated",
                    "message": "Endpoint updated",
                    "id": ep_id,
                    "request_id": "ABCdef789",
                },
            },
        },
        metadata={"ep_id": ep_id},
    )


@pytest.fixture(scope="session", autouse=True)
def _update_guest_responses():
    share_id = str(uuid.uuid1())
    register_response_set(
        "gcp_update_guest",
        {
            "default": {
                "service": "transfer",
                "path": f"/endpoint/{share_id}",
                "method": "PUT",
                "json": {
                    "DATA_TYPE": "endpoint_update_result",
                    "code": "Updated",
                    "message": "Endpoint updated",
                    "id": share_id,
                    "request_id": "ABCdef789",
                },
            },
        },
        metadata={"share_id": share_id},
    )


@pytest.mark.parametrize(
    "addopts, expect_payload_fields",
    (
        (["--display-name", "My Cool GCP"], {"display_name": "My Cool GCP"}),
        (["--public"], {"public": True}),
        (["--private"], {"public": False}),
        (
            ["--subscription-admin-verified", "true"],
            {"subscription_admin_verified": True},
        ),
    ),
)
def test_gcp_update_mapped(run_line, addopts, expect_payload_fields):
    meta = load_response_set("gcp_update_mapped").metadata
    result = run_line(["globus", "gcp", "update", "mapped", meta["ep_id"]] + addopts)
    assert result.output == "Endpoint updated\n"

    sent_data = json.loads(get_last_request().body)
    for key, value in expect_payload_fields.items():
        assert key in sent_data, f"key={key} is present in payload"
        assert sent_data[key] == value, f"key={key} in payload has expected value"

    # check that the 'public' bool opt is correctly filtered out if not provided
    if not ("--public" in addopts or "--private" in addopts):
        assert "public" not in sent_data


@pytest.mark.parametrize(
    "addopts, expect_payload_fields",
    (
        (["--keywords", "foo,bar,baz"], {"keywords": "foo,bar,baz"}),
        (["--display-name", "frobulator"], {"display_name": "frobulator"}),
        (
            ["--subscription-admin-verified", "true"],
            {"subscription_admin_verified": True},
        ),
    ),
)
def test_gcp_update_guest(run_line, addopts, expect_payload_fields):
    meta = load_response_set("gcp_update_guest").metadata
    result = run_line(["globus", "gcp", "update", "mapped", meta["share_id"]] + addopts)
    assert result.output == "Endpoint updated\n"

    sent_data = json.loads(get_last_request().body)
    for key, value in expect_payload_fields.items():
        assert key in sent_data, f"key={key} is present in payload"
        assert sent_data[key] == value, f"key={key} in payload has expected value"
