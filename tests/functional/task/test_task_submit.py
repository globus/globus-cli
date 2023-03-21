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
