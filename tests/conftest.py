import logging
import os
import re
import shlex
import time
import urllib.parse
from unittest import mock

import globus_sdk
import pytest
import responses
from click.testing import CliRunner
from globus_sdk.tokenstorage import SQLiteAdapter
from globus_sdk.transport import RequestsTransport
from globus_sdk.utils import slash_join
from ruamel.yaml import YAML

import globus_cli

yaml = YAML()
log = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def set_login_manager_testmode():
    globus_cli.login_manager.LoginManager._TEST_MODE = True


@pytest.fixture(scope="session")
def go_ep1_id():
    return "ddb59aef-6d04-11e5-ba46-22000b92c6ec"


@pytest.fixture(scope="session")
def go_ep2_id():
    return "ddb59af0-6d04-11e5-ba46-22000b92c6ec"


@pytest.fixture(scope="session")
def task_id():
    return "549ef13c-600f-11eb-9608-0afa7b051b85"


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
    }
    return mock_token_res


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


@pytest.fixture(scope="session")
def test_file_dir():
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "files"))


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


@pytest.fixture
def register_api_route(mocked_responses):
    # copied almost verbatim from the SDK testsuite
    def func(
        service,
        path,
        method=responses.GET,
        adding_headers=None,
        replace=False,
        match_querystring=False,
        **kwargs,
    ):
        base_url_map = {
            "auth": "https://auth.globus.org/",
            "nexus": "https://nexus.api.globusonline.org/",
            "transfer": "https://transfer.api.globus.org/v0.10",
            "search": "https://search.api.globus.org/",
            "gcs": "https://abc.xyz.data.globus.org/api",
            "groups": "https://groups.api.globus.org/v2/",
        }
        assert service in base_url_map
        base_url = base_url_map.get(service)
        full_url = slash_join(base_url, path)

        # can set it to `{}` explicitly to clear the default
        if adding_headers is None:
            adding_headers = {"Content-Type": "application/json"}

        if replace:
            responses.replace(
                method,
                full_url,
                headers=adding_headers,
                match_querystring=match_querystring,
                **kwargs,
            )
        else:
            responses.add(
                method,
                full_url,
                headers=adding_headers,
                match_querystring=match_querystring,
                **kwargs,
            )

    return func


def _iter_fixture_routes(routes):
    # walk a fixture file either as a list of routes
    for x in routes:
        # copy and remove elements
        params = dict(x)
        path = params.pop("path")
        method = params.pop("method", "get")
        yield path, method, params


@pytest.fixture
def load_api_fixtures(register_api_route, test_file_dir, go_ep1_id, go_ep2_id, task_id):
    def func(filename):
        filename = os.path.join(test_file_dir, "api_fixtures", filename)
        with open(filename) as fp:
            data = yaml.load(fp.read())
        for service, routes in data.items():
            # allow use of the key "metadata" to expose extra data from a fixture file
            # to the user of it
            if service == "metadata":
                continue

            for path, method, params in _iter_fixture_routes(routes):
                # allow /endpoint/{GO_EP1_ID} as a path
                use_path = path.format(
                    GO_EP1_ID=go_ep1_id, GO_EP2_ID=go_ep2_id, TASK_ID=task_id
                )
                if "query_params" in params:
                    # copy and set match_querystring=True
                    params = dict(match_querystring=True, **params)
                    # remove and encode query params
                    query_params = urllib.parse.urlencode(params.pop("query_params"))
                    # modify path (assume no prior params)
                    use_path = use_path + "?" + query_params
                print(
                    f"debug: register_api_route({service}, {use_path}, {method}, ...)"
                )
                register_api_route(service, use_path, method=method.upper(), **params)

        # after registration, return the raw fixture data
        return data

    return func


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
