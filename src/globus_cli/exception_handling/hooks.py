from __future__ import annotations

import json
import typing as t

import click
import globus_sdk

from globus_cli.endpointish import WrongEntityTypeError
from globus_cli.login_manager import MissingLoginError
from globus_cli.termio import PrintableErrorField, write_error_info
from globus_cli.utils import CLIAuthRequirementsError

from .registry import error_handler


def _pretty_json(data: dict, compact=False) -> str:
    if compact:
        return json.dumps(data, separators=(",", ":"), sort_keys=True)
    return json.dumps(data, indent=2, separators=(",", ": "), sort_keys=True)


@error_handler(
    error_class=CLIAuthRequirementsError,
    exit_status=4,
)
def handle_internal_auth_requirements(exception: CLIAuthRequirementsError) -> None:
    if not exception.required_scopes:
        click.secho(
            "Fatal Error: Unsupported internal auth requirements error!",
            bold=True,
            fg="red",
        )
        click.get_current_context().exit(255)
    _concrete_consent_required_hook(exception.message, exception.required_scopes)


@error_handler(
    error_class="GlobusAPIError",
    condition=lambda err: err.info.authorization_parameters,
    exit_status=4,
)
def session_hook(exception: globus_sdk.GlobusAPIError) -> None:
    """
    Expects an exception with a valid authorization_paramaters info field
    """
    click.echo(
        "The resource you are trying to access requires you to "
        "re-authenticate with specific identities."
    )

    message = exception.info.authorization_parameters.session_message
    if message:
        click.echo(f"message: {message}")

    identities = exception.info.authorization_parameters.session_required_identities
    domains = exception.info.authorization_parameters.session_required_single_domain
    policies = exception.info.authorization_parameters.session_required_policies

    if identities or domains:
        # cast: mypy can't deduce that `domains` is not None if `identities` is None
        update_target = (
            " ".join(identities)
            if identities
            else " ".join(t.cast(t.List[str], domains))
        )
        click.echo(
            "Please run\n\n"
            f"    globus session update {update_target}\n\n"
            "to re-authenticate with the required identities"
        )
    elif policies:
        click.echo(
            "Please run\n\n"
            f"    globus session update --policy '{','.join(policies)}'\n\n"
            "to re-authenticate with the required identities"
        )
    else:
        click.echo(
            'Please use "globus session update" to re-authenticate '
            "with specific identities"
        )


@error_handler(
    error_class="GlobusAPIError",
    condition=lambda err: err.info.consent_required,
    exit_status=4,
)
def consent_required_hook(exception: globus_sdk.GlobusAPIError) -> None:
    """
    Expects an exception with a required_scopes field in its raw_json
    """
    _concrete_consent_required_hook(
        exception.message, exception.info.consent_required.required_scopes
    )


def _concrete_consent_required_hook(
    message: str | None, required_scopes: list[str]
) -> None:
    # specialized message for data_access errors
    # otherwise, use more generic phrasing
    if message == "Missing required data_access consent":
        click.echo(
            "The collection you are trying to access data on requires you to "
            "grant consent for the Globus CLI to access it."
        )
    else:
        click.echo(
            "The resource you are trying to access requires you to "
            "consent to additional access for the Globus CLI."
        )
    if message:
        click.echo(f"message: {message}")

    if not required_scopes:
        click.secho(
            "Fatal Error: ConsentRequired but no required_scopes!", bold=True, fg="red"
        )
        click.get_current_context().exit(255)
    else:
        click.echo(
            "\nPlease run\n\n"
            "  globus session consent {}\n\n".format(
                " ".join(f"'{x}'" for x in required_scopes)
            )
            + "to login with the required scopes"
        )


@error_handler(
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
    write_error_info(
        "No Authentication Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
        message=(
            "Globus CLI Error: No Authentication provided. Make sure "
            "you have logged in with 'globus login'."
        ),
    )


@error_handler(error_class="TransferAPIError")
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


@error_handler(
    error_class="SearchAPIError",
    condition=lambda err: err.code == "BadRequest.ValidationError",
)
def searchapi_validationerror_hook(exception: globus_sdk.SearchAPIError) -> None:
    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        # FIXME: raw_json because SDK is not exposing `request_id` as an attribute
        PrintableErrorField("request_id", (exception.raw_json or {}).get("request_id")),
        PrintableErrorField("code", exception.code),
        PrintableErrorField("message", exception.message, multiline=True),
    ]
    # FIXME: type cast because error_data type is incorrect
    # (needs upstream fix in SDK)
    error_data = t.cast(t.Optional[dict], exception.error_data)
    if error_data is not None:
        messages = error_data.get("messages")
        if messages is not None and len(messages) == 1:
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


@error_handler(error_class="SearchAPIError")
def searchapi_hook(exception: globus_sdk.SearchAPIError) -> None:
    fields = [
        PrintableErrorField("HTTP status", exception.http_status),
        # FIXME: raw_json because SDK is not exposing `request_id` as an attribute
        PrintableErrorField("request_id", (exception.raw_json or {}).get("request_id")),
        PrintableErrorField("code", exception.code),
        PrintableErrorField("message", exception.message, multiline=True),
    ]
    # FIXME: type cast because error_data type is incorrect
    # (needs upstream fix in SDK)
    error_data = t.cast(t.Optional[dict], exception.error_data)
    if error_data is not None:
        fields += [
            PrintableErrorField("error_data", _pretty_json(error_data, compact=True))
        ]

    write_error_info("Search API Error", fields)


@error_handler(
    error_class="AuthAPIError",
    condition=lambda err: err.message == "invalid_grant",
)
def invalidrefresh_hook(exception: globus_sdk.AuthAPIError) -> None:
    write_error_info(
        "Invalid Refresh Token",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
        message=(
            "Globus CLI Error: Your credentials are no longer "
            "valid. Please log in again with 'globus login'."
        ),
    )


@error_handler(error_class="AuthAPIError")
def authapi_hook(exception: globus_sdk.AuthAPIError) -> None:
    write_error_info(
        "Auth API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@error_handler(error_class="GlobusAPIError")  # catch-all
def globusapi_hook(exception: globus_sdk.GlobusAPIError) -> None:
    write_error_info(
        "Globus API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@error_handler(error_class="GlobusError")
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


def register_all_hooks() -> None:
    """
    This is a stub method which does nothing.

    Importing and running it serves to ensure that the various hooks were imported,
    however. It therefore "looks imperative" and ensures that the hooks are loaded.
    """
