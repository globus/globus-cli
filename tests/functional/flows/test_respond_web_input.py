from __future__ import annotations

import json

from globus_sdk.testing import get_last_request, load_response


def test_respond_web_input_with_option_id(run_line):
    loaded_response = load_response("flows.respond_to_web_input")
    meta = loaded_response.metadata
    web_input_id = meta["web_input_id"]
    option_id = meta["option_id"]

    result = run_line(
        ["globus", "flows", "web-input", "respond", web_input_id, option_id]
    )
    assert "Status:" in result.output
    assert "ok" in result.output

    req = get_last_request()
    sent_body = json.loads(req.body)
    assert sent_body == {"response": {"value": option_id}}
