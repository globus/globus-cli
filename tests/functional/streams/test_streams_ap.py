import json

import pytest
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_streams_get_ap(run_line, output_format):
    meta = load_response_set("cli.streams_access_point").metadata
    result = run_line(
        [
            "globus",
            "streams",
            "access-point",
            "show",
            meta["stream_access_point_id"],
            "-F",
            output_format,
        ]
    )
    if output_format == "json":
        res = json.loads(result.output)
        assert res["data"]["attributes"]["contact_email"] == meta["contact_email"]
        assert res["data"]["attributes"]["display_name"] == meta["display_name"]
        assert res["data"]["id"] == meta["stream_access_point_id"]
    else:
        assert meta["stream_access_point_id"] in result.output
        assert meta["display_name"] in result.output
        assert meta["contact_email"] in result.output
