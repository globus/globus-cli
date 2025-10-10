import json
import uuid

import pytest
from globus_sdk.testing import (
    get_last_request,
    load_response_set,
    register_response_set,
)


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
@pytest.mark.parametrize(
    "addopts, expect_payload_fields",
    (
        ([], {"display_name": "mygcp"}),
        (["--public"], {"display_name": "mygcp", "public": True}),
    ),
)
def test_gcp_create_mapped(run_line, output_format, addopts, expect_payload_fields):
    meta = load_response_set("gcp_create_mapped").metadata
    result = run_line(
        ["globus", "gcp", "create", "mapped", "mygcp", "-F", output_format] + addopts
    )
    if output_format == "json":
        res = json.loads(result.output)
        assert res["DATA_TYPE"] == "endpoint_create_result"
        assert res["code"] == "Created"
        assert res["id"] == meta["ep_id"]
    else:
        assert meta["ep_id"] in result.output
        assert meta["setup_key"] in result.output

    sent_data = json.loads(get_last_request().body)
    for key, value in expect_payload_fields.items():
        assert key in sent_data, f"key={key} is present in payload"
        assert sent_data[key] == value, f"key={key} in payload has expected value"


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


@pytest.mark.parametrize("gcp_type", ["guest", "mapped"])
@pytest.mark.parametrize("deprecated_opt", ["--disable-verify", "--no-disable-verify"])
def test_gcp_create_with_deprecated_verify_option(
    monkeypatch, run_line, gcp_type, deprecated_opt
):
    # force interactive and patch detection methods to get command hints to print
    monkeypatch.setenv("GLOBUS_CLI_INTERACTIVE", "1")
    monkeypatch.setattr("globus_cli.termio.err_is_terminal", lambda: True)
    monkeypatch.setattr("globus_cli.termio.out_is_terminal", lambda: True)

    if gcp_type == "guest":
        meta = load_response_set("gcp_create_guest").metadata
        addopts = f"{meta['host_id']}:/~/ "
    else:
        meta = load_response_set("gcp_create_mapped").metadata
        addopts = ""

    result = run_line(f"globus gcp create {gcp_type} mygcp {addopts}{deprecated_opt}")

    if gcp_type == "mapped":
        assert meta["ep_id"] in result.output
        assert meta["setup_key"] in result.output
    else:
        assert meta["share_id"] in result.output

    # warning was shown
    assert "'--disable-verify/--no-disable-verify' is deprecated" in result.stderr
    # sent data should include 'disable_verify: <option-value>'
    sent_data = json.loads(get_last_request().body)
    assert "disable_verify" in sent_data
    assert sent_data["disable_verify"] == (deprecated_opt == "--disable-verify")
