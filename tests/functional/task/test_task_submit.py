import json

from globus_sdk._testing import load_response_set


def test_filter_rules(run_line, go_ep1_id, go_ep2_id):
    """
    Submits two --exclude and two --include options on a transfer, confirms
    they show up the correct order in --dry-run output
    """
    # put a submission ID and autoactivate response in place
    load_response_set("cli.get_submission_id")
    load_response_set("cli.transfer_activate_success")

    result = run_line(
        "globus transfer -F json --dry-run -r "
        "--exclude foo --include bar "
        "--include baz --exclude qux "
        "{}:/ {}:/".format(go_ep1_id, go_ep1_id)
    )

    expected_filter_rules = [
        {
            "DATA_TYPE": "filter_rule",
            "method": "exclude",
            "name": "foo",
            "type": "file",
        },
        {
            "DATA_TYPE": "filter_rule",
            "method": "include",
            "name": "bar",
            "type": "file",
        },
        {
            "DATA_TYPE": "filter_rule",
            "method": "include",
            "name": "baz",
            "type": "file",
        },
        {
            "DATA_TYPE": "filter_rule",
            "method": "exclude",
            "name": "qux",
            "type": "file",
        },
    ]

    json_output = json.loads(result.output)
    assert json_output["filter_rules"] == expected_filter_rules


def test_exlude_recursive(run_line, go_ep1_id, go_ep2_id):
    """
    Confirms using --exclude on non recursive transfers raises errors
    """
    # would be better if this could fail before we make any api calls, but
    # we want to build the transfer_data object before we parse batch input
    load_response_set("cli.get_submission_id")
    result = run_line(
        "globus transfer --exclude *.txt " "{}:/ {}:/".format(go_ep1_id, go_ep1_id),
        assert_exit_code=2,
    )
    assert (
        "--include and --exclude can only be used with --recursive transfers"
        in result.stderr
    )


def test_exlude_recursive_batch_stdin(run_line, go_ep1_id, go_ep2_id):
    load_response_set("cli.get_submission_id")
    result = run_line(
        "globus transfer --exclude *.txt --batch - "
        "{}:/ {}:/".format(go_ep1_id, go_ep1_id),
        stdin="abc /def\n",
        assert_exit_code=2,
    )
    assert (
        "--include and --exclude can only be used with --recursive transfers"
        in result.stderr
    )


def test_exlude_recursive_batch_file(run_line, go_ep1_id, go_ep2_id, tmp_path):
    load_response_set("cli.get_submission_id")
    temp = tmp_path / "batch"
    temp.write_text("abc /def\n")
    result = run_line(
        [
            "globus",
            "transfer",
            "--exclude",
            "*.txt",
            "--batch",
            temp,
            f"{go_ep1_id}:/",
            f"{go_ep1_id}:/",
        ],
        assert_exit_code=2,
    )
    assert (
        "--include and --exclude can only be used with --recursive transfers"
        in result.stderr
    )


def test_transfer_local_user_opts(run_line, go_ep1_id, go_ep2_id):
    """
    confirms --source-local-user and --destination-local-user are present in
    transfer dry-run output
    """
    load_response_set("cli.get_submission_id")

    result = run_line(
        "globus transfer -F json --dry-run -r "
        "--source-local-user src-user --destination-local-user dst-user "
        f"{go_ep1_id}:/ {go_ep1_id}:/"
    )

    json_output = json.loads(result.output)
    assert json_output["source_local_user"] == "src-user"
    assert json_output["destination_local_user"] == "dst-user"


def test_delete_local_user(run_line, go_ep1_id):
    """
    confirms --local-user is present in delete dry-run output
    """
    load_response_set("cli.get_submission_id")

    result = run_line(
        f"globus delete -F json --dry-run -r --local-user my-user {go_ep1_id}:/"
    )

    json_output = json.loads(result.output)
    assert json_output["local_user"] == "my-user"


def test_rm_local_user(run_line, go_ep1_id):
    """
    confirms --local-user is present in rm dry-run output
    """
    load_response_set("cli.get_submission_id")

    result = run_line(
        f"globus rm -F json --dry-run -r --local-user my-user {go_ep1_id}:/"
    )

    json_output = json.loads(result.output)
    assert json_output["local_user"] == "my-user"
