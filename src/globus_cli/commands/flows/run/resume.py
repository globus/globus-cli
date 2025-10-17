from __future__ import annotations

import textwrap
import typing as t
import uuid

import click
import globus_sdk

from globus_cli.commands.flows._fields import flow_run_format_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import display
from globus_cli.utils import CLIAuthRequirementsError

# NB: GARE parsing requires other SDK components and therefore needs to be deferred to
# avoid the performance impact of non-lazy imports
if t.TYPE_CHECKING:
    from globus_sdk.gare import GARE


@command("resume")
@run_id_arg
@click.option(
    "--skip-inactive-reason-check",
    is_flag=True,
    default=False,
    help=(
        'Skip the check of the run\'s "inactive reason", '
        "which is used to determine what action is required to resume the run."
    ),
)
@LoginManager.requires_login("auth", "flows")
def resume_command(
    login_manager: LoginManager, *, run_id: uuid.UUID, skip_inactive_reason_check: bool
) -> None:
    """
    Resume a run.
    """
    flows_client = login_manager.get_flows_client()
    auth_client = login_manager.get_auth_client()
    run_doc = flows_client.get_run(run_id)
    flow_id = run_doc["flow_id"]

    specific_flow_client = login_manager.get_specific_flow_client(flow_id)

    gare = _get_inactive_reason(run_doc)
    if not skip_inactive_reason_check:
        check_inactive_reason(login_manager, run_id, gare)

    res = specific_flow_client.resume_run(run_id)

    fields = flow_run_format_fields(auth_client, res.data)

    display(res, fields=fields, text_mode=display.RECORD)


def check_inactive_reason(
    login_manager: LoginManager,
    run_id: uuid.UUID,
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
                "This run is missing a necessary consent in order to resume.",
                gare=gare,
            )

    # at this point, the required_scopes may have been checked and satisfied
    # therefore, we should check if there are additional requirements other than
    # the scopes/consents
    unhandled_requirements = set(gare.authorization_parameters.to_dict()) - {
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
            "This run has additional authentication requirements that must be met "
            "in order to resume.",
            gare=gare,
            epilog=textwrap.dedent(
                f"""\
                After updating your session, resume the run with

                    globus flows run resume --skip-inactive-reason-check {run_id}
                """
            ),
        )


def _get_inactive_reason(
    run_doc: dict[str, t.Any] | globus_sdk.GlobusHTTPResponse,
) -> GARE | None:
    from globus_sdk.gare import to_gare

    if not run_doc.get("status") == "INACTIVE":
        return None

    details = run_doc.get("details")
    if not isinstance(details, dict):
        return None

    return to_gare(details)


def _has_required_consent(
    login_manager: LoginManager, required_scopes: list[str]
) -> bool:
    auth_client = login_manager.get_auth_client()
    user_identity_id = login_manager.get_current_identity_id()
    consents = auth_client.get_consents(user_identity_id).to_forest()
    return consents.meets_scope_requirements(required_scopes)
