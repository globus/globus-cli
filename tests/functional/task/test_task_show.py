import uuid

from globus_sdk.testing import load_response_set

ID_ZERO = uuid.UUID(int=0)


def test_skipped_errors(run_line):
    """
    Confirms --skipped-errors option for task show parses the output of
    GET /task/<task_id>/skipped_errors
    """
    meta = load_response_set("cli.skipped_error_list").metadata

    result = run_line(f"globus task show --skipped-errors {meta['task_id']}")
    assert "/~/no-such-file" in result.output
    assert "FILE_NOT_FOUND" in result.output
    assert "/~/restricted-file" in result.output
    assert "PERMISSION_DENIED" in result.output


def test_mutex_options(run_line):
    result = run_line(
        f"globus task show --skipped-errors --successful-transfers {ID_ZERO}",
        assert_exit_code=2,
    )
    assert (
        "--successful-transfers and --skipped-errors are mutually exclusive"
        in result.stderr
    )
