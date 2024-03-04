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


def test_stat_not_found(run_line):
    """
    operation_stat returns a NotFound error, confirm non-error output
    """
    meta = load_response(
        globus_sdk.TransferClient.operation_stat, case="not_found"
    ).metadata
    endpoint_id = meta["endpoint_id"]

    result = run_line(f"globus stat {endpoint_id}:foo/")

    assert result.output == "Nothing found at foo/\n"


def test_stat_permission_denied(run_line):
    """
    operation_stat hits a permission denied error, confirm error output
    """
    meta = load_response(
        globus_sdk.TransferClient.operation_stat, case="permission_denied"
    ).metadata
    endpoint_id = meta["endpoint_id"]

    result = run_line(f"globus stat {endpoint_id}:foo/", assert_exit_code=1)

    assert "A Transfer API Error Occurred." in result.stderr
    assert "EndpointPermissionDenied" in result.stderr
