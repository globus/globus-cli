import json

import pytest
from globus_sdk.testing import RegisteredResponse


def test_base_json_hook(run_line):
    """
    Confirms that the base json hook captures the error JSON and prints it verbatim.
    """
    response = RegisteredResponse(
        service="transfer",
        path="/foo",
        status=400,
        json={"bar": "baz"},
    ).add()
    result = run_line("globus api transfer GET /foo -Fjson", assert_exit_code=1)
    assert response.json == json.loads(result.stderr)


@pytest.mark.parametrize("output_format", ("json", "text"))
def test_base_json_hook_when_no_body_is_present(run_line, output_format):
    """
    Confirms that the base json hook captures the error JSON and prints it verbatim.
    """
    RegisteredResponse(
        service="transfer",
        path="/foo",
        status=500,
        json=None,
    ).add()

    add_opts = []
    if output_format == "json":
        add_opts = ["-Fjson"]

    result = run_line(
        ["globus", "api", "transfer", "GET", "/foo", *add_opts], assert_exit_code=1
    )

    if output_format == "json":
        assert json.loads(result.stderr) == {
            "error_name": "GlobusAPINullDataError",
            "error_type": "TransferAPIError",
        }
    else:
        assert "GlobusAPINullDataError" in result.stderr
        assert "TransferAPIError" in result.stderr
