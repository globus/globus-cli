from __future__ import annotations

import json
import typing as t

import click
import globus_sdk

from globus_cli import termio, version
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, group, mutex_option_group
from globus_cli.termio import display


class QueryParamType(click.ParamType):
    def get_metavar(self, param):
        return "Key=Value"

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        if value is None:
            return None
        if "=" not in value:
            self.fail("invalid query param", param=param, ctx=ctx)
        left, right = value.split("=", 1)
        return (left, right)


class HeaderParamType(click.ParamType):
    def get_metavar(self, param):
        return "Key:Value"

    def convert(self, value, param, ctx):
        value = super().convert(value, param, ctx)
        if value is None:
            return None
        if ":" not in value:
            self.fail("invalid header param", param=param, ctx=ctx)
        left, right = value.split(":", 1)
        if right.startswith(" "):
            right = right[1:]
        return (left, right)


def _looks_like_form(body: str) -> bool:
    # very weak detection for form-encoded data
    # if it's a single line of non-whitespace data with at least one '=', that will do!
    body = body.strip()
    if "\n" in body:
        return False
    if "=" not in body:
        return False
    return True


def _looks_like_json(body: str) -> bool:
    try:
        json.loads(body)
        return True
    except ValueError:
        return False


def detect_content_type(content_type: str, body: str | None) -> str | None:
    if content_type == "json":
        return "application/json"
    elif content_type == "form":
        return "application/x-www-form-urlencoded"
    elif content_type == "text":
        return "text/plain"
    elif content_type == "auto":
        if body is not None:
            if _looks_like_json(body):
                return "application/json"
            if _looks_like_form(body):
                return "application/x-www-form-urlencoded"
        return None
    else:
        raise NotImplementedError(f"did not recognize content-type '{content_type}'")


def print_error_or_response(
    data: globus_sdk.GlobusHTTPResponse | globus_sdk.GlobusAPIError,
) -> None:
    if termio.is_verbose():
        # if verbose, reconstruct the status line and show headers
        click.echo(f"HTTP/1.1 {data.http_status} {data.http_reason}")
        for key in data.headers:
            click.echo(f"{key}: {data.headers[key]}")
        click.echo()
    # raw_text/text must be used here, to present the exact data which was sent, with
    # whitespace and other detail preserved
    if isinstance(data, globus_sdk.GlobusAPIError):
        click.echo(data.raw_text)
    else:
        # however, we will pass this through display using 'simple_text' to get
        # the right semantics
        # specifically: respect `--jmespath` and pretty-print JSON if `-Fjson` is used
        display(data, simple_text=data.text)


_SERVICE_MAP = {
    "auth": LoginManager.AUTH_RS,
    "flows": LoginManager.FLOWS_RS,
    "groups": LoginManager.GROUPS_RS,
    "search": LoginManager.SEARCH_RS,
    "transfer": LoginManager.TRANSFER_RS,
    "timer": LoginManager.TIMER_RS,
}


def _get_client(
    login_manager: LoginManager, service_name: str
) -> globus_sdk.BaseClient:
    if service_name == "auth":
        return login_manager.get_auth_client()
    elif service_name == "flows":
        return login_manager.get_flows_client()
    elif service_name == "groups":
        return login_manager.get_groups_client()
    elif service_name == "search":
        return login_manager.get_search_client()
    elif service_name == "transfer":
        return login_manager.get_transfer_client()
    elif service_name == "timer":
        return login_manager.get_timer_client()
    else:
        raise NotImplementedError(f"unrecognized service: {service_name}")


def _get_url(service_name: str) -> str:
    return {
        "auth": "https://auth.globus.org/",
        "flows": "https://flows.automate.globus.org/",
        "groups": "https://groups.api.globus.org/v2/",
        "search": "https://search.api.globus.org/",
        "transfer": "https://transfer.api.globus.org/v0.10/",
        "timer": "https://timer.automate.globus.org/",
    }[service_name]


@group("api")
def api_command() -> None:
    """Make API calls to Globus services"""


# note: this must be written as a separate call and not inlined into the loop body
# this ensures that it acts as a closure over 'service_name'
def build_command(service_name: str) -> click.Command:
    @command(
        service_name,
        help=f"""\
Make API calls to Globus {service_name.title()}

The arguments are an HTTP method name and a path within the service to which the request
should be made. The path will be joined with the known service URL.
For example, a call of

    globus api {service_name} GET /foo/bar

sends a 'GET' request to '{_get_url(service_name)}foo/bar'
""",
    )
    @LoginManager.requires_login(_SERVICE_MAP[service_name])
    @click.argument(
        "method",
        type=click.Choice(
            ("HEAD", "GET", "PUT", "POST", "PATCH", "DELETE"), case_sensitive=False
        ),
    )
    @click.argument("path")
    @click.option(
        "--query-param",
        "-Q",
        type=QueryParamType(),
        multiple=True,
        help="A query parameter, given as 'key=value'. Use this option multiple "
        "times to pass multiple query parameters.",
    )
    @click.option(
        "--content-type",
        type=click.Choice(("json", "form", "text", "none", "auto")),
        default="auto",
        help="Use a specific Content-Type header for the request. "
        "The default (auto) detects a content type from the data being included in "
        "the request body, while the other names refer to common data encodings. "
        "Any explicit Content-Type header set via '--header' will override this",
    )
    @click.option(
        "--header",
        "-H",
        type=HeaderParamType(),
        multiple=True,
        help="A header, specified as 'Key: Value'. Use this option multiple "
        "times to pass multiple headers.",
    )
    @click.option("--body", help="A request body to include, as text")
    @click.option(
        "--body-file",
        type=click.File("r"),
        help="A request body to include, as a file. Mutually exclusive with --body",
    )
    @click.option(
        "--allow-errors",
        is_flag=True,
        help="Allow error responses (4xx and 5xx) to be displayed without "
        "triggering normal error handling",
    )
    @click.option(
        "--allow-redirects",
        "--location",
        "-L",
        is_flag=True,
        help="If the server responds with a redirect (a 3xx response with a Location "
        "header), follow the redirect. By default, redirects are not followed.",
    )
    @click.option("--no-retry", is_flag=True, help="Disable built-in request retries")
    @mutex_option_group("--body", "--body-file")
    def service_command(
        *,
        login_manager: LoginManager,
        method: str,
        path: str,
        query_param: list[tuple[str, str]],
        header: list[tuple[str, str]],
        body: str | None,
        body_file: t.TextIO | None,
        content_type: str,
        allow_errors: bool,
        allow_redirects: bool,
        no_retry: bool,
    ):
        # the overall flow of this command will be as follows:
        # - prepare a client
        # - prepare parameters for the request
        # - send the request capturing any error raised
        # - process the response
        #   - on success or error with --allow-errors, print
        #   - on error without --allow-errors, reraise

        client = _get_client(login_manager, service_name)
        client.app_name = version.app_name + " raw-api-command"
        if no_retry:
            client.transport.max_retries = 0

        # Prepare Query Params
        query_params_d = {}
        for param_name, param_value in query_param:
            query_params_d[param_name] = param_value

        # Prepare Request Body
        # the value in 'body' will be passed in the request
        # it is intentional that if neither `--body` nor `--body-file` is given,
        # then `body=None`
        if body_file:
            body = body_file.read()

        # Prepare Headers
        # order of evaluation here matters
        # first we process any Content-Type directive, especially for the default case
        # of --content-type=auto
        # after that, apply any manually provided headers, ensuring that they have
        # higher precedence
        #
        # this also makes the behavior well-defined if a user passes
        #
        #   --content-type=json -H "Content-Type: application/octet-stream"
        #
        # the explicit header wins and this is intentional and internally documented
        headers_d = {}
        if content_type != "none":
            detected_content_type = detect_content_type(content_type, body)
            if detected_content_type is not None:
                headers_d["Content-Type"] = detected_content_type
        for header_name, header_value in header:
            headers_d[header_name] = header_value

        # try sending and handle any error
        try:
            res = client.request(
                method.upper(),
                path,
                query_params=query_params_d,
                data=body,
                headers=headers_d,
                allow_redirects=allow_redirects,
            )
        except globus_sdk.GlobusAPIError as e:
            if not allow_errors:
                raise
            # we're in the allow-errors case, so print the HTTP response
            print_error_or_response(e)
        else:
            print_error_or_response(res)

    return t.cast(click.Command, service_command)


for service_name in _SERVICE_MAP:
    api_command.add_command(build_command(service_name))
