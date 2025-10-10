import json

from globus_sdk.testing import load_response_set


def test_jmespath_noop(run_line):
    """
    Runs some simple fetch operations and confirms that `--jmespath '@'`
    doesn't change the output (but also that it overrides --format TEXT)
    """
    meta = load_response_set("cli.endpoint_operations").metadata
    epid = meta["endpoint_id"]
    result = run_line(f"globus endpoint show {epid} -Fjson")
    jmespathresult = run_line(f"globus endpoint show {epid} -Ftext --jmespath '@'")

    assert result.output == jmespathresult.output


def test_jmespath_extract_from_list(run_line, go_ep2_id):
    """
    Uses jmespath to extract a value from a list result using a filter.
    Confirms that the result is identical to a direct fetch of that
    resource.
    """
    load_response_set("cli.endpoint_operations")
    # list tutorial endpoints with a search, but extract go#ep2
    result = run_line(
        (
            "globus endpoint search 'Tutorial' --jmespath \"DATA[?id=='{}'] | [0]\""
        ).format(go_ep2_id)
    )
    outputdict = json.loads(result.output)

    show_result = run_line(f"globus endpoint show {go_ep2_id} -Fjson")
    showdict = json.loads(show_result.output)

    # check specific keys because search includes `_rank` and doesn't
    # include the server list
    # just a semi-random selection of values for this test
    for k in ("id", "display_name", "owner_id", "subscription_id"):
        assert outputdict[k] == showdict[k]


def test_jmespath_no_expression_error(run_line):
    """
    Intentionally misuse `--jmespath` with no provided expression. Confirm
    that it gives a usage error.
    """
    result = run_line(
        "globus endpoint search 'Tutorial' --jmespath", assert_exit_code=2
    )
    assert "Error: Option '--jmespath' requires an argument" in result.stderr

    # and the error says `--jq` if you use the `--jq` form
    result = run_line("globus endpoint search 'Tutorial' --jq", assert_exit_code=2)
    assert "Error: Option '--jq' requires an argument" in result.stderr


def test_jmespath_invalid_expression_error(run_line):
    """
    Intentionally misuse `--jmespath` with a malformed expression. Confirm
    that it gives a JMESPath ParseError.
    """
    result = run_line(
        "globus endpoint search 'Tutorial' --jmespath '{}'", assert_exit_code=1
    )
    assert "ParseError:" in result.stderr
