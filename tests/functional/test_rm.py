import json

import responses
from globus_sdk._testing import load_response_set


def _get_delete_call():
    # get the delete call, parse the body, and return both
    try:
        delete_call = next(
            r.request for r in responses.calls if r.request.url.endswith("/delete")
        )
    except StopIteration:
        return None, None
    sent_data = json.loads(delete_call.body)
    return delete_call, sent_data


def _load_probably_json_substring(x):
    """
    Weak method of extracting JSON object from a string which includes JSON and
    non-JSON data. Just gets the largest substring from { to }
    Works well for these cases, where click.CliRunner gives us output
    containing both stderr and stdout.
    """
    return json.loads(x[x.index("{") : x.rindex("}") + 1])


def test_recursive(run_line, go_ep1_id):
    """
    Makes a dir on ep1, then --recursive rm's it.
    Confirms delete task was successful.
    """
    load_response_set("cli.get_submission_id")
    load_response_set("cli.submit_delete_success")

    result = run_line(f"globus rm -r -F json {go_ep1_id}:/foo")
    res = _load_probably_json_substring(result.output)
    assert res["status"] == "SUCCEEDED"


def test_no_file(run_line, go_ep1_id):
    """
    Attempts to remove a non-existent file. Confirms exit code 1.
    """
    load_response_set("cli.get_submission_id")
    load_response_set("cli.submit_delete_failed")

    run_line(f"globus rm {go_ep1_id}:/nosuchfile.txt", assert_exit_code=1)

    # confirm that we sent `ignore_missing=False`
    # makes sense in context with the ignore-missing test below
    _delete_call, sent_data = _get_delete_call()
    assert sent_data["ignore_missing"] is False


def test_ignore_missing(run_line, go_ep1_id):
    """
    Attempts to remove a non-existent file path, with --ignore-missing.
    Confirms exit code 0 and silent output.
    """
    load_response_set("cli.get_submission_id")
    load_response_set("cli.submit_delete_success")

    path = "/~/nofilehere.txt"
    result = run_line(f"globus rm -f {go_ep1_id}:{path}")
    assert "Delete task submitted under ID " in result.stderr

    # confirm that we sent `ignore_missing=True`
    _delete_call, sent_data = _get_delete_call()
    assert sent_data["ignore_missing"] is True


def test_timeout(run_line, go_ep1_id):
    """
    If a task is retrying without success, `rm` should wait and eventually time out.
    """
    load_response_set("cli.get_submission_id")
    load_response_set("cli.submit_delete_queued")

    result = run_line(
        f"globus rm -r --timeout 2 {go_ep1_id}:/foo/bar.txt",
        assert_exit_code=1,
    )
    assert "Task has yet to complete after 2 seconds" in result.stderr


def test_timeout_explicit_status(run_line, go_ep1_id):
    """
    As above, submit a task which sits queued and times out.
    Confirms rm exits STATUS after given timeout, where
    STATUS is set via the --timeout-exit-code opt
    """
    load_response_set("cli.get_submission_id")
    load_response_set("cli.submit_delete_queued")

    status = 50
    result = run_line(
        "globus rm -r --timeout 1 --timeout-exit-code {} {}:/foo/bar.txt".format(
            status, go_ep1_id
        ),
        assert_exit_code=status,
    )
    assert "Task has yet to complete after 1 seconds" in result.stderr
