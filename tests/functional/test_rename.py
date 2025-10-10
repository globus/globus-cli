import json

from globus_sdk.testing import get_last_request, load_response_set


def test_simple_rename_success(run_line, go_ep1_id):
    """
    Just confirm that args make it through the command successfully and we render the
    message as output.
    """
    load_response_set("cli.rename_result")

    result = run_line(f"globus rename {go_ep1_id} foo/bar /baz/buzz")
    assert "File or directory renamed successfully" in result.output


def test_local_user(run_line, go_ep1_id):
    """
    Confirms --local-user makes it to the request body.
    """
    load_response_set("cli.rename_result")

    run_line(f"globus rename {go_ep1_id} foo/bar /baz/buzz --local-user my-user")

    sent_data = json.loads(get_last_request().body)
    assert sent_data["local_user"] == "my-user"
