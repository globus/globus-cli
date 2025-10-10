import urllib.parse

from globus_sdk.testing import (
    RegisteredResponse,
    get_last_request,
    load_response,
    load_response_set,
)


def test_path(run_line, go_ep1_id):
    """
    Does an ls on EP1:/, confirms expected results.
    """
    load_response_set("cli.ls_results")
    result = run_line(f"globus ls {go_ep1_id}:/")

    expected = ["home/", "mnt/", "not shareable/", "share/"]
    for item in expected:
        assert item in result.output


def test_recursive(run_line, go_ep1_id):
    """
    Confirms --recursive ls on EP1:/share/ finds file1.txt .
    """
    load_response_set("cli.ls_results")
    result = run_line(f"globus ls -r {go_ep1_id}:/share")
    assert "file1.txt" in result.output


# regression test for
#   https://github.com/globus/globus-cli/issues/577
def test_recursive_empty(run_line, go_ep1_id):
    """
    Empty recursive ls should have an empty result.
    """
    load_response_set("cli.ls_results")
    result = run_line(f"globus ls -r {go_ep1_id}:/mnt")
    assert result.output.strip() == ""


def test_depth(run_line, go_ep1_id):
    """
    Confirms setting depth to 1 on a --recursive ls of EP1:/
    finds godata but not file1.txt
    """
    load_response_set("cli.ls_results")
    result = run_line(f"globus ls -r --recursive-depth-limit 1 {go_ep1_id}:/")
    assert "file1.txt" not in result.output


def test_recursive_json(run_line, go_ep1_id):
    """
    Confirms -F json works with the RecursiveLsResponse.
    """
    load_response_set("cli.ls_results")
    result = run_line(f"globus ls -r -F json {go_ep1_id}:/share")
    assert '"DATA":' in result.output
    assert '"name": "godata/file1.txt"' in result.output


def test_local_user(run_line, go_ep1_id):
    """
    Confirms --local-user is passed to query params.
    """
    load_response_set("cli.ls_results")
    result = run_line(f"globus ls {go_ep1_id}:/~/ -F json --local-user my-user")
    assert '"user": "my-user"' in result.output


def test_recursive_and_orderby_mutex(run_line, go_ep1_id):
    result = run_line(
        f"globus ls {go_ep1_id}:/ --recursive --orderby name:ASC",
        assert_exit_code=2,
    )
    assert "--recursive and --orderby are mutually exclusive" in result.stderr


def test_orderby_encoding(run_line, go_ep1_id):
    """
    Does an ls on EP1:/, but pass `--orderby` and check that it was encoded correctly
    in the request.
    """
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/v0.10/operation/endpoint/{go_ep1_id}/ls",
            json={
                "DATA": [],
            },
        )
    )

    run_line(f"globus ls {go_ep1_id}:/ --orderby size:DESC --orderby name:ASC")

    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_params = urllib.parse.parse_qs(parsed_url.query)
    assert "orderby" in parsed_params
    assert parsed_params["orderby"] == ["size DESC,name ASC"]
