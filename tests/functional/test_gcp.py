import json
import uuid

import pytest
from globus_sdk._testing import load_response_set, register_response_set


@pytest.fixture(scope="session", autouse=True)
def _create_mapped_responses():
    ep_id = str(uuid.uuid1())
    setup_key = str(uuid.uuid1())
    register_response_set(
        "gcp_create_mapped",
        {
            "default": {
                "service": "transfer",
                "path": "/endpoint",
                "method": "POST",
                "json": {
                    "DATA_TYPE": "endpoint_create_result",
                    "code": "Created",
                    "message": "Endpoint created",
                    "globus_connect_setup_key": setup_key,
                    "id": ep_id,
                    "request_id": "ABCdef789",
                },
            },
        },
        metadata={"ep_id": ep_id, "setup_key": setup_key},
    )


@pytest.fixture(scope="session", autouse=True)
def _create_guest_responses():
    host_id = str(uuid.uuid1())
    share_id = str(uuid.uuid1())
    register_response_set(
        "gcp_create_guest",
        {
            "activate_host": {
                "service": "transfer",
                "path": f"/endpoint/{host_id}/autoactivate",
                "method": "POST",
                "json": {"code": "AutoActivated.BogusCode"},
            },
            "share_create": {
                "service": "transfer",
                "path": "/shared_endpoint",
                "method": "POST",
                "json": {
                    "DATA_TYPE": "endpoint_create_result",
                    "code": "Created",
                    "message": "Shared endpoint created",
                    "id": share_id,
                    "request_id": "ABCdef789",
                },
            },
        },
        metadata={"host_id": host_id, "share_id": share_id},
    )


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_gcp_create_mapped(run_line, output_format):
    meta = load_response_set("gcp_create_mapped").metadata
    result = run_line(f"globus gcp create mapped mygcp -F {output_format}")
    if output_format == "json":
        res = json.loads(result.output)
        assert res["DATA_TYPE"] == "endpoint_create_result"
        assert res["code"] == "Created"
        assert res["id"] == meta["ep_id"]
    else:
        assert meta["ep_id"] in result.output
        assert meta["setup_key"] in result.output


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_gcp_create_share(run_line, output_format):
    meta = load_response_set("gcp_create_guest").metadata
    host_id = meta["host_id"]

    result = run_line(
        f"globus gcp create guest myshare -F {output_format} {host_id}:/~/"
    )
    if output_format == "json":
        res = json.loads(result.output)
        assert res["DATA_TYPE"] == "endpoint_create_result"
        assert res["code"] == "Created"
        assert "Shared endpoint" in res["message"]
        assert res["id"] == meta["share_id"]
    else:
        assert meta["share_id"] in result.output
