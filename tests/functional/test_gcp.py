import json

from globus_sdk._testing import load_response_set


def test_gcp_create_mapped(run_line):
    load_response_set("cli.gcp_create")
    result = run_line("globus gcp create mapped mygcp -F json")
    res = json.loads(result.output)
    assert res["DATA_TYPE"] == "endpoint_create_result"
    assert res["code"] == "Created"
    assert "id" in res


def test_gcp_create_share(run_line):
    load_response_set("cli.endpoint_operations")
    meta = load_response_set("cli.transfer_activate_success").metadata
    epid = meta["endpoint_id"]

    result = run_line(f"globus gcp create guest myshare -F json {epid}:/~/")
    res = json.loads(result.output)
    assert res["DATA_TYPE"] == "endpoint_create_result"
    assert res["code"] == "Created"
    assert "Shared endpoint" in res["message"]
    assert "id" in res
