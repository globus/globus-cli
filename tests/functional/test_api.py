import pytest
from globus_sdk._testing import RegisteredResponse, load_response


@pytest.mark.parametrize(
    "service_name", ["auth", "transfer", "groups", "search", "timer"]
)
@pytest.mark.parametrize("is_error_response", (False, True))
def test_api_command_get(run_line, service_name, is_error_response):
    load_response(
        RegisteredResponse(
            service=service_name,
            status=500 if is_error_response else 200,
            path="/foo",
            json={"foo": "bar"},
        )
    )

    result = run_line(
        ["globus", "api", service_name, "get", "/foo"]
        + (["--no-retry", "--allow-errors"] if is_error_response else [])
    )
    assert result.output == '{"foo": "bar"}\n'


def test_api_command_can_use_jmespath(run_line):
    load_response(
        RegisteredResponse(
            service="transfer",
            status=200,
            path="/foo",
            json={"foo": "bar"},
        )
    )

    result = run_line(["globus", "api", "transfer", "get", "/foo", "--jmespath", "foo"])
    assert result.output == '"bar"\n'
