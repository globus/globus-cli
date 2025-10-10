import pytest
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize("cli_arg", ("task_id", "--all"))
def test_cancel(run_line, cli_arg):
    """Validate task cancellation."""
    meta = load_response_set("cli.task_cancel").metadata
    if cli_arg == "task_id":
        cli_arg = meta["task_id"]
    result = run_line(f"globus task cancel {cli_arg}")
    assert "cancelled successfully" in result.output
