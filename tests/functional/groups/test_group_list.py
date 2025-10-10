from globus_sdk.testing import load_response_set


def test_group_list(run_line):
    """
    Runs globus group list and validates results.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]
    group2_id = meta["group2_id"]
    group1_name = meta["group1_name"]
    group2_name = meta["group2_name"]

    result = run_line("globus group list")

    assert group1_id in result.output
    assert group2_id in result.output
    assert group1_name in result.output
    assert group2_name in result.output
