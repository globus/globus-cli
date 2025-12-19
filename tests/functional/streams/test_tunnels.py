import json

import pytest
from globus_sdk.testing import get_last_request, load_response_set


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_tunnel_create(run_line, output_format):
    meta = load_response_set("cli.tunnel_operations").metadata
    result = run_line(
        [
            "globus",
            "streams",
            "tunnel",
            "create",
            meta["initiator_id"],
            meta["listener_id"],
            "--label",
            meta["display_name"],
            "-F",
            output_format,
        ]
    )
    if output_format == "json":
        res = json.loads(result.output)
        assert res["data"]["attributes"]["label"] == meta["display_name"]
        assert res["data"]["id"] == meta["tunnel_id"]
    else:
        assert meta["tunnel_id"] in result.output

    sent_data = json.loads(get_last_request().body)
    assert sent_data["data"]["attributes"]["label"] == meta["display_name"]
    assert not sent_data["data"]["attributes"]["restartable"]
    assert (
        sent_data["data"]["relationships"]["initiator"]["data"]["id"]
        == meta["initiator_id"]
    )
    assert (
        sent_data["data"]["relationships"]["listener"]["data"]["id"]
        == meta["listener_id"]
    )


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_tunnel_show(run_line, output_format):
    meta = load_response_set("cli.tunnel_operations").metadata
    result = run_line(
        ["globus", "streams", "tunnel", "show", meta["tunnel_id"], "-F", output_format]
    )
    if output_format == "json":
        res = json.loads(result.output)
        assert res["data"]["attributes"]["label"] == meta["display_name"]
        assert res["data"]["id"] == meta["tunnel_id"]
    else:
        assert meta["tunnel_id"] in result.output


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_tunnel_update(run_line, output_format):
    meta = load_response_set("cli.tunnel_operations").metadata
    result = run_line(
        [
            "globus",
            "streams",
            "tunnel",
            "update",
            meta["tunnel_id"],
            "--label",
            meta["display_name"],
            "-F",
            output_format,
        ]
    )
    if output_format == "json":
        res = json.loads(result.output)
        assert res["data"]["attributes"]["label"] == meta["display_name"]
        assert res["data"]["id"] == meta["tunnel_id"]
    else:
        assert meta["tunnel_id"] in result.output

    sent_data = json.loads(get_last_request().body)
    assert sent_data["data"]["attributes"]["label"] == meta["display_name"]
