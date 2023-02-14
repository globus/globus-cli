from __future__ import annotations

import logging
import os
import re
import shlex
import time
import uuid
from unittest import mock

import globus_sdk
import pytest
import responses
from click.testing import CliRunner
from globus_sdk._testing import register_response_set
from globus_sdk.scopes import TimerScopes
from globus_sdk.tokenstorage import SQLiteAdapter
from globus_sdk.transport import RequestsTransport
from ruamel.yaml import YAML

import globus_cli

yaml = YAML()
log = logging.getLogger(__name__)

_test_file_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "files"))


def pytest_configure(config):
    _register_all_response_sets()


@pytest.fixture(autouse=True)
def mocksleep():
    with mock.patch("time.sleep") as m:
        yield m


@pytest.fixture(autouse=True)
def disable_login_manager_validate_token():
    def fake_validate_token(self, token):
        return True

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(
            globus_cli.login_manager.LoginManager,
            "_validate_token",
            fake_validate_token,
        )
        yield mp


@pytest.fixture(scope="session")
def go_ep1_id():
    return "ddb59aef-6d04-11e5-ba46-22000b92c6ec"


@pytest.fixture(scope="session")
def go_ep2_id():
    return "ddb59af0-6d04-11e5-ba46-22000b92c6ec"


def _mock_token_response_data(rs_name, scope, token_blob=None):
    if token_blob is None:
        token_blob = rs_name.split(".")[0]
    return {
        "scope": scope,
        "refresh_token": f"{token_blob}RT",
        "access_token": f"{token_blob}AT",
        "token_type": "bearer",
        "expires_at_seconds": int(time.time()) + 120,
        "resource_server": rs_name,
    }


@pytest.fixture
def mock_login_token_response():
    mock_token_res = mock.Mock()
    mock_token_res.by_resource_server = {
        "auth.globus.org": _mock_token_response_data(
            "auth.globus.org",
            "openid profile email "
            "urn:globus:auth:scope:auth.globus.org:view_identity_set",
        ),
        "transfer.api.globus.org": _mock_token_response_data(
            "transfer.api.globus.org",
            "urn:globus:auth:scope:transfer.api.globus.org:all",
        ),
        "groups.api.globus.org": _mock_token_response_data(
            "groups.api.globus.org", "urn:globus:auth:scope:groups.api.globus.org:all"
        ),
        "search.api.globus.org": _mock_token_response_data(
            "search.api.globus.org", "urn:globus:auth:scope:search.api.globus.org:all"
        ),
        TimerScopes.resource_server: _mock_token_response_data(
            TimerScopes.resource_server, TimerScopes.timer
        ),
        "flows.globus.org": _mock_token_response_data(
            "flows.globus.org",
            scope=(
                "https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/manage_flows "  # noqa E501
                "https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/view_flows "  # noqa E501
                "https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/run "  # noqa E501
                "https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/run_status "  # noqa E501
                "https://auth.globus.org/scopes/eec9b274-0c81-4334-bdc2-54e90e689b9a/run_manage "  # noqa E501
            ),
        ),
    }
    return mock_token_res


@pytest.fixture
def client_login(monkeypatch):
    monkeypatch.setenv("GLOBUS_CLI_CLIENT_ID", "fake_client_id")
    monkeypatch.setenv("GLOBUS_CLI_CLIENT_SECRET", "fake_client_secret")


@pytest.fixture()
def client_login_no_secret(monkeypatch):
    monkeypatch.setenv("GLOBUS_CLI_CLIENT_ID", "fake_client_id")


@pytest.fixture()
def user_profile(monkeypatch):
    monkeypatch.setenv("GLOBUS_PROFILE", "test_user_profile")


@pytest.fixture
def test_token_storage(mock_login_token_response):
    """Put memory-backed sqlite token storage in place for the testsuite to use."""
    mockstore = SQLiteAdapter(":memory:")
    mockstore.store_config(
        "auth_client_data",
        {"client_id": "fakeClientIDString", "client_secret": "fakeClientSecret"},
    )
    mockstore.store(mock_login_token_response)
    return mockstore


@pytest.fixture(autouse=True)
def patch_tokenstorage(monkeypatch, test_token_storage):
    monkeypatch.setattr(
        globus_cli.login_manager.token_storage_adapter,
        "_instance",
        test_token_storage,
        raising=False,
    )


@pytest.fixture
def add_gcs_login(test_token_storage):
    def func(gcs_id):
        mock_token_res = mock.Mock()
        mock_token_res.by_resource_server = {
            gcs_id: _mock_token_response_data(
                gcs_id, f"urn:globus:auth:scopes:{gcs_id}:manage_collections"
            )
        }
        test_token_storage.store(mock_token_res)

    return func


@pytest.fixture
def add_flow_login(test_token_storage):
    def func(flow_id: uuid.UUID | str):
        scopes = globus_sdk.SpecificFlowClient(flow_id).scopes
        mock_token_res = mock.Mock()
        mock_token_res.by_resource_server = {
            scopes.resource_server: _mock_token_response_data(
                scopes.resource_server, [scopes.user]
            )
        }
        test_token_storage.store(mock_token_res)

    return func


@pytest.fixture(scope="session")
def test_file_dir():
    return _test_file_dir


@pytest.fixture
def cli_runner():
    return CliRunner(mix_stderr=False)


class OutputMatcher:
    r"""
    A helper for running regex matches and optionally doing literal checking of match
    groups against expected strings. This can be attached to run_line by passing
    "matcher=True".

    Runs regex matches in multiline mode, operating on the first match.
    If no match is found, it will raise an error.

    Usage:

    >>> res, matcher = run_line(..., matcher=True)
    >>> matcher.check(r"^Foo:\s+(\w+)$", groups=["FooValue"])
    """

    def __init__(self, result):
        self._result = result

    def check(self, regex, groups=None, err=False) -> None:
        pattern = re.compile(regex, flags=re.MULTILINE)
        groups = groups or []
        data = self._result.stderr if err else self._result.output

        m = pattern.search(data)
        if not m:
            raise ValueError(f"Did not find a match for '{regex}' in {data}")
        for i, x in enumerate(groups, 1):
            assert m.group(i) == x


@pytest.fixture
def run_line(cli_runner, request, patch_tokenstorage):
    """
    Uses the CliRunner to run the given command line.

    Asserts that the exit_code is equal to the given assert_exit_code,
    and if that exit_code is 0 prevents click from catching exceptions
    for easier debugging.
    """

    def func(line, assert_exit_code=0, stdin=None, matcher=False):
        from globus_cli import main

        # split line into args and confirm line starts with "globus"
        args = shlex.split(line) if isinstance(line, str) else line
        assert args[0] == "globus"

        # run the line. globus_cli.main is the "globus" part of the line
        # if we are expecting success (0), don't catch any exceptions.
        result = cli_runner.invoke(
            main, args[1:], input=stdin, catch_exceptions=bool(assert_exit_code)
        )
        if result.exit_code != assert_exit_code:
            raise (
                Exception(
                    (
                        "CliTest run_line exit_code assertion failed!\n"
                        "Line:\n{}\nexited with {} when expecting {}\n"
                        "stdout:\n{}\nstderr:\n{}\nnetwork calls recorded:"
                        "\n  {}"
                    ).format(
                        line,
                        result.exit_code,
                        assert_exit_code,
                        result.stdout,
                        result.stderr,
                        (
                            "\n  ".join(
                                f"{r.request.method} {r.request.url}"
                                for r in responses.calls
                            )
                            or "  <none>"
                        ),
                    )
                )
            )
        if matcher:
            return result, OutputMatcher(result)
        return result

    return func


@pytest.fixture(autouse=True)
def mocked_responses(monkeypatch):
    """
    All tests enable `responses` patching of the `requests` package, replacing
    all HTTP calls.
    """
    responses.start()

    # while request mocking is running, ensure GLOBUS_SDK_ENVIRONMENT is set to
    # production
    monkeypatch.setitem(os.environ, "GLOBUS_SDK_ENVIRONMENT", "production")

    yield

    responses.stop()
    responses.reset()


def _iter_fixture_routes(routes):
    # walk a fixture file either as a list of routes
    for x in routes:
        # copy and remove elements
        params = dict(x)
        path = params.pop("path")
        method = params.pop("method", "get")
        yield path, method, params


def _register_all_response_sets():
    fixture_dir = os.path.join(_test_file_dir, "api_fixtures")

    def do_register(filename):
        with open(os.path.join(fixture_dir, filename)) as fp:
            data = yaml.load(fp.read())

        response_set = {}
        response_set_metadata = {}
        for service, routes in data.items():
            if service == "metadata":
                response_set_metadata = routes
                continue

            for idx, (path, method, params) in enumerate(_iter_fixture_routes(routes)):
                if "query_params" in params:
                    # TODO: remove this int/float conversion after we upgrade to
                    # `responses>=0.19.0` when this issue is expected to be fixed
                    #   https://github.com/getsentry/responses/pull/485
                    query_params = {
                        k: str(v) if isinstance(v, (int, float)) else v
                        for k, v in params.pop("query_params").items()
                    }
                    params["match"] = [
                        responses.matchers.query_param_matcher(query_params)
                    ]
                response_set[f"{method}_{service}_{path}_{idx}"] = {
                    "service": service,
                    "path": path,
                    "method": method.upper(),
                    **params,
                }

        scenario_name = filename.rsplit(".", 1)[0]
        register_response_set(
            f"cli.{scenario_name}", response_set, metadata=response_set_metadata
        )

    for filename in os.listdir(fixture_dir):
        if not filename.endswith(".yaml"):
            continue
        do_register(filename)


@pytest.fixture(autouse=True)
def disable_client_retries(monkeypatch):
    class NoRetryTransport(RequestsTransport):
        DEFAULT_MAX_RETRIES = 0

    monkeypatch.setattr(globus_sdk.TransferClient, "transport_class", NoRetryTransport)
    monkeypatch.setattr(globus_sdk.AuthClient, "transport_class", NoRetryTransport)
    monkeypatch.setattr(
        globus_sdk.NativeAppAuthClient, "transport_class", NoRetryTransport
    )
    monkeypatch.setattr(
        globus_sdk.ConfidentialAppAuthClient, "transport_class", NoRetryTransport
    )
