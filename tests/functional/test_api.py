import urllib.parse

import pytest
from globus_sdk._testing import (
    RegisteredResponse,
    get_last_request,
    load_response,
    register_response_set,
)


@pytest.fixture(scope="module", autouse=True)
def _register_stub_transfer_response():
    register_response_set(
        "cli.api.transfer_stub",
        {
            "default": {
                "service": "transfer",
                "status": 200,
                "path": "/foo",
                "json": {"foo": "bar"},
            }
        },
    )


@pytest.mark.parametrize(
    "service_name", ["auth", "flows", "groups", "search", "timer", "transfer"]
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
    load_response("cli.api.transfer_stub")

    result = run_line(["globus", "api", "transfer", "get", "/foo", "--jmespath", "foo"])
    assert result.output == '"bar"\n'


def test_api_command_query_param(run_line):
    load_response("cli.api.transfer_stub")

    result = run_line(
        ["globus", "api", "transfer", "get", "/foo", "-Q", "frobulation_mode=reversed"]
    )
    assert result.output == '{"foo": "bar"}\n'

    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_query_string = urllib.parse.parse_qs(parsed_url.query)
    assert parsed_query_string == {"frobulation_mode": ["reversed"]}


def test_api_command_query_params_multiple_become_list(run_line):
    load_response("cli.api.transfer_stub")

    result = run_line(
        [
            "globus",
            "api",
            "transfer",
            "get",
            "/foo",
            "-Q",
            "filter=frobulated",
            "-Q",
            "filter=demuddled",
            "-Q",
            "filter=reversed",
        ]
    )
    assert result.output == '{"foo": "bar"}\n'

    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_query_string = urllib.parse.parse_qs(parsed_url.query)
    assert list(parsed_query_string.keys()) == ["filter"]
    assert set(parsed_query_string["filter"]) == {"frobulated", "demuddled", "reversed"}
