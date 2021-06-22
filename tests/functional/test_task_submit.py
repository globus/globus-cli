import json


def test_exclude(run_line, load_api_fixtures, go_ep1_id, go_ep2_id):
    """
    Submits two --exclude options on a transfer, confirms they show up
    in --dry-run output
    """
    # put a submission ID and autoactivate response in place
    load_api_fixtures("get_submission_id.yaml")
    load_api_fixtures("transfer_activate_success.yaml")

    result = run_line(
        "globus transfer -F json --dry-run -r "
        "--exclude *.txt --exclude *.pdf "
        "{}:/ {}:/".format(go_ep1_id, go_ep1_id)
    )

    expected_filter_rules = [
        {"DATA_TYPE": "filter_rule", "method": "exclude", "name": "*.txt"},
        {"DATA_TYPE": "filter_rule", "method": "exclude", "name": "*.pdf"},
    ]

    json_output = json.loads(result.output)
    assert json_output["filter_rules"] == expected_filter_rules


def test_exlude_recursive(run_line, load_api_fixtures, go_ep1_id, go_ep2_id):
    """
    Confirms using --exclude on non recursive transfers raises errors
    """
    # would be better if this could fail before we make any api calls, but
    # we want to build the transfer_data object before we parse batch input
    load_api_fixtures("get_submission_id.yaml")

    expected_error = "--exclude can only be used with --recursive transfers"

    # single
    result = run_line(
        "globus transfer --exclude *.txt " "{}:/ {}:/".format(go_ep1_id, go_ep1_id),
        assert_exit_code=2,
    )
    assert expected_error in result.stderr

    # batch
    batch_input = "abc /def\n"
    result = run_line(
        "globus transfer --exclude *.txt --batch "
        "{}:/ {}:/".format(go_ep1_id, go_ep1_id),
        stdin=batch_input,
        assert_exit_code=2,
    )
    assert expected_error in result.stderr
