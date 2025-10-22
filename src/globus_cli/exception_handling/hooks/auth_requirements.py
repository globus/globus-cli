from __future__ import annotations

import click
import globus_sdk

from globus_cli.login_manager import MissingLoginError
from globus_cli.utils import CLIAuthRequirementsError

from ..messages import (
    DEFAULT_CONSENT_REAUTH_MESSAGE,
    DEFAULT_SESSION_REAUTH_MESSAGE,
    emit_consent_required_message,
    emit_message_for_gare,
    emit_session_update_message,
)
from ..registry import error_handler, sdk_error_handler


@error_handler(error_class=CLIAuthRequirementsError, exit_status=4)
def handle_internal_auth_requirements(
    exception: CLIAuthRequirementsError,
) -> int | None:
    gare = exception.gare
    if not gare:
        msg = "Fatal Error: Unsupported internal auth requirements error!"
        click.secho(msg, bold=True, fg="red")
        return 255

    emit_message_for_gare(gare, exception.message)

    if exception.epilog:
        click.echo("\n* * *\n")
        click.echo(exception.epilog)

    return None


@sdk_error_handler(
    condition=lambda err: bool(err.info.authorization_parameters), exit_status=4
)
def session_hook(exception: globus_sdk.GlobusAPIError) -> None:
    """
    Expects an exception with a valid authorization_parameters info field.
    """
    message = exception.info.authorization_parameters.session_message
    if message:
        message = f"{DEFAULT_SESSION_REAUTH_MESSAGE}\nmessage: {message}"
    else:
        message = DEFAULT_SESSION_REAUTH_MESSAGE

    emit_session_update_message(
        identities=exception.info.authorization_parameters.session_required_identities,
        domains=exception.info.authorization_parameters.session_required_single_domain,
        policies=exception.info.authorization_parameters.session_required_policies,
        message=message,
    )
    return None


@sdk_error_handler(condition=lambda err: bool(err.info.consent_required), exit_status=4)
def consent_required_hook(exception: globus_sdk.GlobusAPIError) -> int | None:
    """
    Expects an exception with a required_scopes field in its raw_json.
    """
    if not exception.info.consent_required.required_scopes:
        msg = (
            "Fatal Error: A ConsentRequired error was encountered "
            "but the error did not contain a required_scopes field!"
        )
        click.secho(msg, bold=True, fg="red")
        return 255

    # specialized message for data_access errors
    # otherwise, use more generic phrasing
    if exception.message == "Missing required data_access consent":
        message = (
            "The collection you are trying to access data on requires you to "
            "grant consent for the Globus CLI to access it."
        )
    else:
        message = f"{DEFAULT_CONSENT_REAUTH_MESSAGE}\nMessage: {exception.message}"

    emit_consent_required_message(
        required_scopes=exception.info.consent_required.required_scopes, message=message
    )
    return None


@error_handler(error_class=MissingLoginError, exit_status=4)
def missing_login_error_hook(exception: MissingLoginError) -> None:
    click.echo(
        click.style("MissingLoginError: ", fg="yellow") + exception.message,
        err=True,
    )
