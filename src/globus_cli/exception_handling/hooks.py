from __future__ import annotations

import json
import textwrap
import typing as t

import click
import globus_sdk
import globus_sdk.gare

from globus_cli.endpointish import WrongEntityTypeError
from globus_cli.login_manager import MissingLoginError
from globus_cli.termio import PrintableErrorField, outformat_is_json, write_error_info
from globus_cli.types import JsonValue
from globus_cli.utils import CLIAuthRequirementsError

from .registry import error_handler, sdk_error_handler


def _pretty_json(data: JsonValue, compact: bool = False) -> str:
    if compact:
        return json.dumps(data, separators=(",", ":"), sort_keys=True)
    return json.dumps(data, indent=2, separators=(",", ": "), sort_keys=True)


_JSONPATH_SPECIAL_CHARS = "[]'\"\\."
_JSONPATH_ESCAPE_MAP = str.maketrans(
    {
        "'": "\\'",
        "\\": "\\\\",
    }
)


def _jsonpath_from_pydantic_loc(loc: list[str | int]) -> str:
    """
    Given a 'loc' from pydantic error data, convert it into a JSON Path expression.

    Takes the following steps:
    - turns integers into integer indices
    - turns most strings into dotted access
    - turns strings containing special characters into single-quoted bracket access
      with ' and \\ escaped
    """
    path = "$"
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            if any(c in part for c in _JSONPATH_SPECIAL_CHARS):
                part = f"'{part.translate(_JSONPATH_ESCAPE_MAP)}'"
                path += f"[{part}]"
            else:
                path += f".{part}"
    return path


_DEFAULT_SESSION_REAUTH_MESSAGE = (
    "The resource you are trying to access requires you to re-authenticate."
)
_DEFAULT_CONSENT_REAUTH_MESSAGE = (
    "The resource you are trying to access requires you to "
    "consent to additional access for the Globus CLI."
)


@sdk_error_handler(
    error_class="GlobusAPIError",
    condition=lambda err: err.raw_json is None,
)
def null_data_error_handler(exception: globus_sdk.GlobusAPIError) -> None:
    write_error_info(
        "GlobusAPINullDataError",
        [PrintableErrorField("error_type", exception.__class__.__name__)],
    )


@sdk_error_handler(
    error_class="GlobusAPIError",
    condition=lambda err: outformat_is_json(),
)
def json_error_handler(exception: globus_sdk.GlobusAPIError) -> None:
    click.echo(
        click.style(
            json.dumps(exception.raw_json, indent=2, separators=(",", ": ")),
            fg="yellow",
        ),
        err=True,
    )


@error_handler(
    error_class=CLIAuthRequirementsError,
    exit_status=4,
)
def handle_internal_auth_requirements(
    exception: CLIAuthRequirementsError,
) -> int | None:
    gare = exception.gare
    if not gare:
        click.secho(
            "Fatal Error: Unsupported internal auth requirements error!",
            bold=True,
            fg="red",
        )
        return 255

    _handle_gare(gare, exception.message)

    if exception.epilog:
        click.echo("\n* * *\n")
        click.echo(exception.epilog)

    return None


@sdk_error_handler(
    error_class="FlowsAPIError",
    condition=lambda err: globus_sdk.gare.is_gare(err.raw_json or {}),
    exit_status=4,
)
def handle_flows_gare(exception: globus_sdk.FlowsAPIError) -> int | None:
    gare = globus_sdk.gare.to_gare(exception.raw_json or {})
    if not gare:
        raise ValueError("Expected a GARE, but got None")

    _handle_gare(gare)

    return None


@sdk_error_handler(
    condition=lambda err: bool(err.info.authorization_parameters),
    exit_status=4,
)
def session_hook(exception: globus_sdk.GlobusAPIError) -> None:
    """
    Expects an exception with a valid authorization_paramaters info field.
    """
    message = exception.info.authorization_parameters.session_message
    if message:
        message = f"{_DEFAULT_SESSION_REAUTH_MESSAGE}\nmessage: {message}"
    else:
        message = _DEFAULT_SESSION_REAUTH_MESSAGE

    return _concrete_session_hook(
        identities=exception.info.authorization_parameters.session_required_identities,
        domains=exception.info.authorization_parameters.session_required_single_domain,
        policies=exception.info.authorization_parameters.session_required_policies,
        message=message,
    )


@sdk_error_handler(
    condition=lambda err: bool(err.info.consent_required),
    exit_status=4,
)
def consent_required_hook(exception: globus_sdk.GlobusAPIError) -> int | None:
    """
    Expects an exception with a required_scopes field in its raw_json.
    """
    if not exception.info.consent_required.required_scopes:
        click.secho(
            "Fatal Error: ConsentRequired but no required_scopes!", bold=True, fg="red"
        )
        return 255

    # specialized message for data_access errors
    # otherwise, use more generic phrasing
    if exception.message == "Missing required data_access consent":
        message = (
            "The collection you are trying to access data on requires you to "
            "grant consent for the Globus CLI to access it."
        )
    else:
        message = f"{_DEFAULT_CONSENT_REAUTH_MESSAGE}\nmessage: {exception.message}"

    _concrete_consent_required_hook(
        required_scopes=exception.info.consent_required.required_scopes,
        message=message,
    )
    return None


def _concrete_session_hook(
    *,
    policies: list[str] | None,
    identities: list[str] | None,
    domains: list[str] | None,
    message: str = _DEFAULT_SESSION_REAUTH_MESSAGE,
) -> None:
    click.echo(message)

    if identities or domains:
        # cast: mypy can't deduce that `domains` is not None if `identities` is None
        update_target = (
            " ".join(identities)
            if identities
            else " ".join(t.cast(t.List[str], domains))
        )
        click.echo(
            "\nPlease run:\n\n"
            f"    globus session update {update_target}\n\n"
            "to re-authenticate with the required identities."
        )
    elif policies:
        click.echo(
            "\nPlease run:\n\n"
            f"    globus session update --policy '{','.join(policies)}'\n\n"
            "to re-authenticate with the required identities."
        )
    else:
        click.echo(
            '\nPlease use "globus session update" to re-authenticate '
            "with specific identities."
        )


def _concrete_consent_required_hook(
    *,
    required_scopes: list[str],
    message: str = _DEFAULT_CONSENT_REAUTH_MESSAGE,
) -> None:
    click.echo(message)

    click.echo(
        "\nPlease run:\n\n"
        "  globus session consent {}\n\n".format(
            " ".join(f"'{x}'" for x in required_scopes)
        )
        + "to login with the required scopes."
    )


@sdk_error_handler(
    condition=lambda err: (
        (
            isinstance(err, globus_sdk.TransferAPIError)
            and err.code == "ClientError.AuthenticationFailed"
        )
        or (isinstance(err, globus_sdk.AuthAPIError) and err.code == "UNAUTHORIZED")
    )
)
def authentication_hook(
    exception: globus_sdk.TransferAPIError | globus_sdk.AuthAPIError,
) -> None:
    click.echo(
        (
            "Globus CLI Error: No Authentication provided. Make sure "
            "you have logged in with 'globus login'."
        ),
        err=True,
    )


@sdk_error_handler(error_class="TransferAPIError")
def transferapi_hook(exception: globus_sdk.TransferAPIError) -> None:
    write_error_info(
        "Transfer API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("request_id", exception.request_id),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@sdk_error_handler(
    error_class="SearchAPIError",
    condition=lambda err: err.code == "BadRequest.ValidationError",
)
def searchapi_validationerror_hook(exception: globus_sdk.SearchAPIError) -> None:
    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        PrintableErrorField("request_id", exception.request_id),
        PrintableErrorField("code", exception.code),
        PrintableErrorField("message", exception.message, multiline=True),
    ]
    error_data: dict[str, JsonValue] | None = exception.error_data
    if error_data is not None:
        messages = error_data.get("messages")
        if isinstance(messages, dict) and len(messages) == 1:
            error_location, details = next(iter(messages.items()))
            fields += [
                PrintableErrorField("location", error_location),
                PrintableErrorField("details", _pretty_json(details), multiline=True),
            ]
        elif messages is not None:
            fields += [
                PrintableErrorField("details", _pretty_json(messages), multiline=True)
            ]

    write_error_info("Search API Error", fields)


@sdk_error_handler(error_class="SearchAPIError")
def searchapi_hook(exception: globus_sdk.SearchAPIError) -> None:
    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        PrintableErrorField("request_id", exception.request_id),
        PrintableErrorField("code", exception.code),
        PrintableErrorField("message", exception.message, multiline=True),
    ]
    error_data: dict[str, JsonValue] | None = exception.error_data
    if error_data is not None:
        fields += [
            PrintableErrorField("error_data", _pretty_json(error_data, compact=True))
        ]

    write_error_info("Search API Error", fields)


@sdk_error_handler(
    error_class="FlowsAPIError",
    condition=lambda err: err.code == "UNPROCESSABLE_ENTITY",
)
def flows_validation_error_hook(exception: globus_sdk.FlowsAPIError) -> None:
    message_string: str = exception.raw_json["error"]["message"]  # type: ignore[index]
    details: str | list[dict[str, t.Any]] = exception.raw_json["error"]["detail"]  # type: ignore[index] # noqa: E501
    message_fields = [PrintableErrorField("message", message_string)]

    # conditionally do this work if there are multiple details
    if isinstance(details, list) and len(details) > 1:
        num_errors = len(details)
        # try to extract 'loc' and 'msg' from the details, but only
        # update 'message_fields' if the data are present
        try:
            messages = [
                f"{_jsonpath_from_pydantic_loc(data['loc'])}: {data['msg']}"
                for data in details
            ]
        except KeyError:
            pass
        else:
            message_fields = [
                PrintableErrorField(
                    "message", f"{num_errors} validation errors", multiline=True
                ),
                PrintableErrorField(
                    "errors",
                    "\n".join(messages),
                    multiline=True,
                ),
            ]

    write_error_info(
        "Flows API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            *message_fields,
        ],
    )


@sdk_error_handler(error_class="FlowsAPIError")
def flows_error_hook(exception: globus_sdk.FlowsAPIError) -> None:
    assert exception.raw_json is not None  # Influence mypy's knowledge of `raw_json`.
    details: list[dict[str, t.Any]] | str = exception.raw_json["error"]["detail"]
    detail_fields: list[PrintableErrorField] = []

    # if the detail is a string, return that as a single field
    if isinstance(details, str):
        if len(details) > 120:
            details = textwrap.fill(details, width=80)
        detail_fields = [PrintableErrorField("detail", details, multiline=True)]
    # if it's a list of objects, wrap them into a multiline detail field
    elif isinstance(details, list):
        num_errors = len(details)
        if all((isinstance(d, dict) and "loc" in d and "msg" in d) for d in details):
            detail_strings = [
                (
                    ((data["type"] + " ") if "type" in data else "")
                    + f"{_jsonpath_from_pydantic_loc(data['loc'])}: {data['msg']}"
                )
                for data in details
            ]
            if num_errors == 1:
                detail_fields = [PrintableErrorField("detail", detail_strings[0])]
            else:
                detail_fields = [
                    PrintableErrorField("detail", f"{num_errors} errors"),
                    PrintableErrorField(
                        "errors",
                        "\n".join(detail_strings),
                        multiline=True,
                    ),
                ]
        else:
            detail_fields = [
                PrintableErrorField(
                    "detail",
                    "\n".join(_pretty_json(detail, compact=True) for detail in details),
                    multiline=True,
                )
            ]

    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        PrintableErrorField("code", exception.code),
    ]
    if "message" in exception.raw_json["error"]:
        fields.append(
            PrintableErrorField("message", exception.raw_json["error"]["message"])
        )
    fields.extend(detail_fields)

    write_error_info("Flows API Error", fields)


@sdk_error_handler(
    error_class="AuthAPIError",
    condition=lambda err: err.message == "invalid_grant",
)
def invalidrefresh_hook(exception: globus_sdk.AuthAPIError) -> None:
    click.echo(
        (
            "Globus CLI Error: Your credentials are no longer "
            "valid. Please log in again with 'globus login'."
        ),
        err=True,
    )


@sdk_error_handler(error_class="AuthAPIError")
def authapi_hook(exception: globus_sdk.AuthAPIError) -> None:
    write_error_info(
        "Auth API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@sdk_error_handler()  # catch-all
def globusapi_hook(exception: globus_sdk.GlobusAPIError) -> None:
    write_error_info(
        "Globus API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@sdk_error_handler(error_class="GlobusError")
def globus_error_hook(exception: globus_sdk.GlobusError) -> None:
    write_error_info(
        "Globus Error",
        [
            PrintableErrorField("error_type", exception.__class__.__name__),
            PrintableErrorField("message", str(exception), multiline=True),
        ],
    )


@error_handler(error_class=WrongEntityTypeError, exit_status=3)
def wrong_endpoint_type_error_hook(exception: WrongEntityTypeError) -> None:
    click.echo(
        click.style(
            exception.expected_message + "\n" + exception.actual_message,
            fg="yellow",
        )
        + "\n\n",
        err=True,
    )

    should_use = exception.should_use_command()
    if should_use:
        click.echo(
            "Please run the following command instead:\n\n"
            f"    {should_use} {exception.endpoint_id}\n",
            err=True,
        )
    else:
        click.echo(
            click.style(
                "This operation is not supported on objects of this type.",
                fg="red",
                bold=True,
            ),
            err=True,
        )


@error_handler(error_class=MissingLoginError, exit_status=4)
def missing_login_error_hook(exception: MissingLoginError) -> None:
    click.echo(
        click.style("MissingLoginError: ", fg="yellow") + exception.message,
        err=True,
    )


def _handle_gare(gare: globus_sdk.gare.GARE, message: str | None = None) -> None:
    required_scopes = gare.authorization_parameters.required_scopes
    if required_scopes:
        _concrete_consent_required_hook(
            required_scopes=required_scopes,
            message=message or _DEFAULT_CONSENT_REAUTH_MESSAGE,
        )

    session_policies = gare.authorization_parameters.session_required_policies
    session_identities = gare.authorization_parameters.session_required_identities
    session_domains = gare.authorization_parameters.session_required_single_domain
    if session_policies or session_identities or session_domains:
        _concrete_session_hook(
            policies=session_policies,
            identities=session_identities,
            domains=session_domains,
            message=message or _DEFAULT_SESSION_REAUTH_MESSAGE,
        )


def register_all_hooks() -> None:
    """
    This is a stub method which does nothing.

    Importing and running it serves to ensure that the various hooks were imported,
    however. It therefore "looks imperative" and ensures that the hooks are loaded.
    """
