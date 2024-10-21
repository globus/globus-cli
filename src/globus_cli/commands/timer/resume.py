from __future__ import annotations

import textwrap
import typing as t
import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.login_manager.utils import get_current_identity_id
from globus_cli.parsing import command
from globus_cli.termio import display
from globus_cli.utils import CLIAuthRequirementsError

# NB: GARE parsing requires other SDK components and therefore needs to be deferred to
# avoid the performance impact of non-lazy imports
if t.TYPE_CHECKING:
    from globus_sdk.gare import GARE


@command("resume", short_help="Resume a timer.")
@click.argument("TIMER_ID", type=click.UUID)
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
    login_manager: LoginManager,
    *,
    timer_id: uuid.UUID,
    skip_inactive_reason_check: bool,
) -> None:
    """
    Resume a timer.
    """
    timer_client = login_manager.get_timer_client()
    timer_doc = timer_client.get_job(timer_id)

    gare = _get_inactive_reason(timer_doc)
    if not skip_inactive_reason_check:
        check_inactive_reason(login_manager, timer_id, gare)

    resumed = timer_client.resume_job(
        timer_id,
        update_credentials=(gare is not None),
    )
    display(resumed, text_mode=display.RAW, simple_text=resumed["message"])


def check_inactive_reason(
    login_manager: LoginManager,
    timer_id: uuid.UUID,
    gare: GARE | None,
) -> None:
    if gare is None:
        return
    if gare.authorization_parameters.required_scopes:
        consent_required = not _has_required_consent(
            login_manager, gare.authorization_parameters.required_scopes
        )
        if consent_required:
            raise CLIAuthRequirementsError(
                "This timer is missing a necessary consent in order to resume.",
                gare=gare,
            )

    # at this point, the required_scopes may have been checked and satisfied
    # therefore, we should check if there are additional requirements other than
    # the scopes/consents
    unhandled_requirements = set(gare.authorization_parameters.to_dict().keys()) - {
        "required_scopes",
        # also remove 'message' -- not a 'requirement'
        "session_message",
    }
    # reraise if anything remains after consent checking
    # this ensures that we will reraise if we get an error which contains
    # both required_scopes and additional requirements
    # (consents may be present without session requirements met)
    if unhandled_requirements:
        raise CLIAuthRequirementsError(
            "This timer has additional authentication requirements that must be met "
            "in order to resume.",
            gare=gare,
            epilog=textwrap.dedent(
                f"""\
                After updating your session, resume the timer with:

                    globus timer resume --skip-inactive-reason-check {timer_id}
                """
            ),
        )


def _get_inactive_reason(
    timer_doc: dict[str, t.Any] | globus_sdk.GlobusHTTPResponse
) -> GARE | None:
    from globus_sdk.gare import to_gare

    if timer_doc.get("status") != "inactive":
        return None

    reason = timer_doc.get("inactive_reason", {})
    if reason.get("cause") != "globus_auth_requirements":
        return None

    return to_gare(reason.get("detail", {}))


def _has_required_consent(
    login_manager: LoginManager, required_scopes: list[str]
) -> bool:
    auth_client = login_manager.get_auth_client()
    user_identity_id = get_current_identity_id()
    consents = auth_client.get_consents(user_identity_id).to_forest()
    return consents.meets_scope_requirements(required_scopes)
