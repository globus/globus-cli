import urllib.parse

import globus_sdk
from globus_sdk._testing import get_last_request, load_response


def test_stat(run_line):
    """
    Make a stat with the --local-user option, confirm output is rendered and query
    parameters are passed as expected
    """
    meta = load_response(globus_sdk.TransferClient.operation_stat).metadata
    endpoint_id = meta["endpoint_id"]

    result = run_line(f"globus stat {endpoint_id}:foo/ --local-user bar")
    expected = """Name:          file1.txt
Type:          file
Last Modified: 2023-12-18 16:52:50+00:00
Size:          4
Permissions:   0644
User:          tutorial
Group:         tutorial
"""
    assert result.output == expected

    req = get_last_request()
    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(req.url).query)
    assert parsed_qs == {"path": ["foo/"], "local_user": ["bar"]}
