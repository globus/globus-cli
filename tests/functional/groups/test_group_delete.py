from globus_sdk.testing import load_response_set


def test_group_delete(run_line):
    """
    Basic success test for globus group delete.
    """
    meta = load_response_set("cli.groups").metadata

    group1_id = meta["group1_id"]

    result = run_line(f"globus group delete {group1_id}")

    assert "Group deleted successfully" in result.output
