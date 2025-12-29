import json

import globus_sdk
import pytest
from globus_sdk.testing import get_last_request, load_response


def test_filter_rules(run_line, go_ep1_id, go_ep2_id):
    """
    Submits two --exclude and two --include options on a transfer, confirms
    they show up the correct order in --dry-run output
    """
    load_response(globus_sdk.TransferClient.get_submission_id)

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


def test_exclude_recursive(run_line, go_ep1_id, go_ep2_id):
    """
    Confirms using --exclude on non recursive transfers raises errors.
    """
    result = run_line(
        f"globus transfer --exclude *.txt {go_ep1_id}:/ {go_ep1_id}:/",
        assert_exit_code=2,
    )
    assert (
        "`--include` and `--exclude` can only be used with `--recursive` transfers"
        in result.stderr
    )


def test_exclude_recursive_batch_stdin(run_line, go_ep1_id, go_ep2_id):
    result = run_line(
        f"globus transfer --exclude *.txt --batch - {go_ep1_id}:/ {go_ep1_id}:/",
        stdin="abc /def\n",
        assert_exit_code=2,
    )
    assert (
        "`--include` and `--exclude` can only be used with `--recursive` transfers"
        in result.stderr
    )


def test_exclude_recursive_batch_file(run_line, go_ep1_id, go_ep2_id, tmp_path):
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
        "`--include` and `--exclude` can only be used with `--recursive` transfers"
        in result.stderr
    )


def test_transfer_local_user_opts(run_line, go_ep1_id, go_ep2_id):
    """
    confirms --source-local-user and --destination-local-user are present in
    transfer dry-run output
    """
    load_response(globus_sdk.TransferClient.get_submission_id)

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
    Confirms --local-user is present in delete dry-run output.
    """
    load_response(globus_sdk.TransferClient.get_submission_id)

    result = run_line(
        f"globus delete -F json --dry-run -r --local-user my-user {go_ep1_id}:/"
    )

    json_output = json.loads(result.output)
    assert json_output["local_user"] == "my-user"


def test_rm_local_user(run_line, go_ep1_id):
    """
    Confirms --local-user is present in rm dry-run output.
    """
    result = run_line(
        f"globus rm -F json --dry-run -r --local-user my-user {go_ep1_id}:/"
    )

    json_output = json.loads(result.output)
    assert json_output["local_user"] == "my-user"


def test_transfer_recursive_options(run_line, go_ep1_id, go_ep2_id, tmp_path):
    """
    Confirm --recursive, --no-recursive, and omission of the --recursive option
    result in the expected values in the transfer item
    """
    load_response(globus_sdk.TransferClient.get_submission_id)

    # --recursive should set the value to True
    result = run_line(
        f"globus transfer --recursive --dry-run -F json {go_ep1_id}:/ {go_ep1_id}:/"
    )
    json_output = json.loads(result.output)
    transfer_item = json_output["DATA"][0]
    assert transfer_item["recursive"] is True

    # --no-recursive should set the value to False
    result = run_line(
        f"globus transfer --no-recursive --dry-run -F json {go_ep1_id}:/ {go_ep1_id}:/"
    )
    json_output = json.loads(result.output)
    transfer_item = json_output["DATA"][0]
    assert transfer_item["recursive"] is False

    # not using the option should omit the field
    result = run_line(f"globus transfer --dry-run -F json {go_ep1_id}:/ {go_ep1_id}:/")
    json_output = json.loads(result.output)
    transfer_item = json_output["DATA"][0]
    assert "recursive" not in transfer_item


@pytest.mark.parametrize("option", ("", "--recursive", "--no-recursive"))
def test_recursion_options_in_batch_input(run_line, go_ep1_id, go_ep2_id, option):
    load_response(globus_sdk.TransferClient.submit_transfer)
    load_response(globus_sdk.TransferClient.get_submission_id)

    stdin = f"abc def {option}\n"
    run_line(
        [
            "globus",
            "transfer",
            "--batch",
            "-",
            f"{go_ep1_id}:/",
            f"{go_ep1_id}:/",
        ],
        stdin=stdin,
    )

    # Retrieve the first DATA item in the JSON request body.
    request = get_last_request()
    item = json.loads(request.body)["DATA"][0]

    # Assert things.
    if option == "--recursive":
        assert item["recursive"] is True
    elif option == "--no-recursive":
        assert item["recursive"] is False
    else:  # option == ""
        assert "recursive" not in item
