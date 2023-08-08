from __future__ import annotations

import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager, read_well_known_config
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import Field, TextMode, display, formatters
from globus_cli.utils import CLIAuthRequirementsError

# NB: GARE parsing requires other SDK components and therefore needs to be deferred to
# avoid the performance impact of non-lazy imports
if t.TYPE_CHECKING:
    from globus_sdk.experimental.auth_requirements_error import (
        GlobusAuthRequirementsError,
    )


@command("resume")
@run_id_arg
@click.option(
    "--skip-inactive-reason-check",
    is_flag=True,
    default=False,
    help='Skip the check of the run\'s "inactive reason", which is used to determine '
    "what action is required to resume the run.",
)
@LoginManager.requires_login("auth", "flows")
def resume_command(
    login_manager: LoginManager, *, run_id: uuid.UUID, skip_inactive_reason_check: bool
) -> None:
    """
    Resume a run
    """
    flows_client = login_manager.get_flows_client()
    run_doc = flows_client.get_run(run_id)
    flow_id = run_doc["flow_id"]

    specific_flow_client = login_manager.get_specific_flow_client(flow_id)

    if not skip_inactive_reason_check:
        gare = _get_inactive_reason(run_doc)
        if gare is not None and gare.authorization_parameters.required_scopes:
            if not _has_required_consent(
                login_manager, gare.authorization_parameters.required_scopes
            ):
                raise CLIAuthRequirementsError(
                    "This run is missing a necessary consent in order to resume.",
                    required_scopes=gare.authorization_parameters.required_scopes,
                )

    fields = [
        Field("Run ID", "run_id"),
        Field("Flow ID", "flow_id"),
        Field("Flow Title", "flow_title"),
        Field("Status", "status"),
        Field("Run Label", "label"),
        Field("Run Tags", "tags", formatter=formatters.Array),
        Field("Started At", "start_time", formatter=formatters.Date),
    ]

    res = specific_flow_client.resume_run(run_id)
    display(res, fields=fields, text_mode=TextMode.text_record)


def _get_inactive_reason(
    run_doc: dict[str, t.Any]
) -> GlobusAuthRequirementsError | None:
    from globus_sdk.experimental.auth_requirements_error import (
        to_auth_requirements_error,
    )

    if not run_doc.get("status") == "INACTIVE":
        return None

    details = run_doc.get("details")
    if not isinstance(details, dict):
        return None

    return to_auth_requirements_error(details)


def _has_required_consent(
    login_manager: LoginManager, required_scopes: list[str]
) -> bool:
    auth_client = login_manager.get_auth_client()
    user_data = read_well_known_config("auth_user_data", allow_null=False)
    user_identity_id = user_data["sub"]
    consents = auth_client.get_consents(user_identity_id)
    return consents.contains_scopes(required_scopes)
