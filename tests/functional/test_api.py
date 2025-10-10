import urllib.parse
import uuid

import pytest
import responses
from globus_sdk.testing import (
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
    "service_name",
    ["gcs", "auth", "flows", "groups", "search", "timers", "timer", "transfer"],
)
@pytest.mark.parametrize("is_error_response", (False, True))
def test_api_command_get(run_line, service_name, add_gcs_login, is_error_response):
    sdk_service_name = "timer" if service_name == "timers" else service_name
    load_response(
        RegisteredResponse(
            service=sdk_service_name,
            status=500 if is_error_response else 200,
            path="/foo",
            json={"foo": "bar"},
        )
    )
    service_args = [service_name]

    if service_name == "gcs":
        endpoint_id = str(uuid.uuid1())
        load_response(
            RegisteredResponse(
                service="transfer",
                path=f"/v0.10/endpoint/{endpoint_id}",
                # this data contains the GCS server hostname which is baked into
                # globus_sdk.testing, so there's some "magical" data coordination at
                # play here
                json={
                    "DATA": [
                        {"DATA_TYPE": "server", "hostname": "abc.xyz.data.globus.org"}
                    ],
                    "gcs_manager_url": "https://abc.xyz.data.globus.org",
                    "entity_type": "GCSv5_endpoint",
                },
            )
        )
        service_args.append(endpoint_id)
        add_gcs_login(endpoint_id)

    result = run_line(
        ["globus", "api", *service_args, "get", "/foo"]
        + (["--no-retry", "--allow-errors"] if is_error_response else [])
    )
    assert result.output == '{"foo": "bar"}\n'


def test_api_groups_v2_path_stripping(run_line):
    load_response(
        RegisteredResponse(
            service="groups",
            status=200,
            path="/foo",
            json={"foo": "bar"},
        )
    )

    result = run_line(["globus", "api", "groups", "get", "/v2/foo"])
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


def test_api_command_with_scope_strings(monkeypatch, client_login, run_line):
    load_response("cli.api.transfer_stub")
    load_response("auth.oauth2_client_credentials_tokens")

    run_line("globus api transfer get /foo --scope-string foobarjohn")

    token_grant = [
        call for call in responses.calls if call.request.url.endswith("/token")
    ][0]
    request_params = urllib.parse.parse_qs(token_grant.request.body)
    assert request_params["grant_type"][0] == "client_credentials"
    scopes = request_params["scope"][0].split(" ")
    # This is the default transfer scope, inherited through the service name.
    assert "urn:globus:auth:scope:transfer.api.globus.org:all" in scopes
    # This is the scope string we explicitly passed in.
    assert "foobarjohn" in scopes


def test_api_command_rejects_non_client_based_scope_strings(run_line):
    result = run_line(
        "globus api auth GET /v2/api/projects --scope-string foobarjohn",
        assert_exit_code=2,
    )
    assert "only supported for confidential-client authorized calls" in result.stderr
