from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager, read_well_known_config
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display
from globus_cli.utils import CLIAuthRequirementsError

# NB: GARE parsing requires other SDK components and therefore needs to be deferred to
# avoid the performance impact of non-lazy imports
if t.TYPE_CHECKING:
    from globus_sdk.experimental.auth_requirements_error import (
        GlobusAuthRequirementsError,
    )


@command("resume", short_help="Resume a timer")
@click.argument("JOB_ID", type=click.UUID)
@click.option(
    "--skip-inactive-reason-check",
    is_flag=True,
    default=False,
    help=(
        'Skip the check of the timer\'s "inactive reason", which is used to determine '
        "if additional steps are required to successfully resume the timer."
    ),
)
@LoginManager.requires_login("timer")
def resume_command(
    login_manager: LoginManager, *, job_id: uuid.UUID, skip_inactive_reason_check: bool
) -> None:
    """
    Resume a timer.
    """
    timer_client = login_manager.get_timer_client()
    job_doc = timer_client.get_job(job_id)

    if not skip_inactive_reason_check:
        gare = _get_inactive_reason(job_doc)
        if gare is not None and gare.authorization_parameters.required_scopes:
            if not _has_required_consent(
                login_manager, gare.authorization_parameters.required_scopes
            ):
                raise CLIAuthRequirementsError(
                    "This run is missing a necessary consent in order to resume.",
                    required_scopes=gare.authorization_parameters.required_scopes,
                )

    resumed = timer_client.resume_job(
        job_id,
        update_credentials=(not skip_inactive_reason_check),
    )
    display(
        resumed,
        text_mode=TextMode.text_raw,
        simple_text=resumed["message"],
    )


def _get_inactive_reason(
    job_doc: dict[str, t.Any] | globus_sdk.GlobusHTTPResponse
) -> GlobusAuthRequirementsError | None:
    from globus_sdk.experimental.auth_requirements_error import (
        to_auth_requirements_error,
    )

    if not job_doc.get("status") == "inactive":
        return None

    reason = job_doc.get("inactive_reason", {})
    if reason.get("cause") != "globus_auth_requirements":
        return None

    return to_auth_requirements_error(reason.get("detail", {}))


def _has_required_consent(
    login_manager: LoginManager, required_scopes: list[str]
) -> bool:
    auth_client = login_manager.get_auth_client()
    user_data = read_well_known_config("auth_user_data", allow_null=False)
    user_identity_id = user_data["sub"]
    consents = auth_client.get_consents(user_identity_id)
    return consents.contains_scopes(required_scopes)
