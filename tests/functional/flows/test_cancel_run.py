from globus_sdk._testing import load_response


def test_cancel_run_text_output(run_line):
    cancel_response = load_response("flows.cancel_run")
    run_id = cancel_response.metadata["run_id"]

    result = run_line(f"globus flows run cancel {run_id}")
    # Verify all fields are present.
    for fieldname in (
        "Flow ID",
        "Flow Title",
        "Run ID",
        "Run Label",
        "Started At",
        "Completed At",
        "Status",
    ):
        assert fieldname in result.output
