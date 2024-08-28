import json

import globus_sdk
from globus_sdk._testing import get_last_request, load_response


def test_simple_mkdir_success(run_line):
    """
    Just confirm that args make it through the command successfully and we render the
    message as output.
    """
    meta = load_response(globus_sdk.TransferClient.operation_mkdir).metadata
    endpoint_id = meta["endpoint_id"]

    result = run_line(f"globus mkdir {endpoint_id}:foo/")
    assert "The directory was created successfully" in result.output


def test_local_user(run_line):
    """
    Confirms --local-user makes it to the request body.
    """
    meta = load_response(globus_sdk.TransferClient.operation_mkdir).metadata
    endpoint_id = meta["endpoint_id"]

    run_line(f"globus mkdir {endpoint_id}:foo/ --local-user my-user")

    sent_data = json.loads(get_last_request().body)
    assert sent_data["local_user"] == "my-user"
