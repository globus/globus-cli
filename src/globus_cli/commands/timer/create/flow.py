from __future__ import annotations

import datetime
import textwrap
import uuid

import click
import globus_sdk
from globus_sdk.scopes import Scope, SpecificFlowScopeBuilder, TimersScopes

from globus_cli.login_manager import LoginManager, is_client_login
from globus_cli.parsing import (
    ParsedJSONData,
    command,
    flow_id_arg,
    flow_input_document_option,
)
from globus_cli.termio import display

from ._common import CREATE_FORMAT_FIELDS, TimerSchedule, timer_schedule_options


@command("flow", short_help="Create a recurring flow timer.")
@flow_id_arg
@flow_input_document_option
@click.option("--name", type=str, help="A name for the timer.")
@timer_schedule_options
@LoginManager.requires_login("auth", "flows", "timers")
def flow_command(
    login_manager: LoginManager,
    *,
    flow_id: uuid.UUID,
    input_document: ParsedJSONData | None,
    name: str | None,
    schedule: TimerSchedule,
) -> None:
    """
    Create a timer that runs a flow on a recurring schedule.

    \b\bExamples (assume the year is 1970, when time began):

    Create a timer which runs a flow daily for the next 10 days.

        globus timer create flow $flow_id --interval 1d --stop-after-runs 10

    Create a timer which runs a flow every week for the rest of the year.

        globus timer create flow $flow_id --interval 7d --stop-after-date 1970-12-31

    Create a timer which runs a flow once on Christmas.

        globus timer create flow $flow_id --start 1970-12-25 --stop-after-runs 1
    """
    if name is None:
        now = datetime.datetime.now().isoformat()
        name = f"CLI Created Timer [{now}]"

    verify_flow_exists(login_manager, flow_id)
    verify_requester_has_required_consents(login_manager, flow_id)

    timer_doc = globus_sdk.FlowTimer(
        flow_id=flow_id,
        name=name,
        schedule=schedule,
        body={"body": input_document or {}},
    )
    response = login_manager.get_timer_client().create_timer(timer_doc)

    display(response["timer"], text_mode=display.RECORD, fields=CREATE_FORMAT_FIELDS)


def verify_flow_exists(login_manager: LoginManager, flow_id: uuid.UUID) -> None:
    """
    Verify that the flow with the given ID exists.

    If it does not exist, print an error message and exit.
    """
    try:
        flow_client = login_manager.get_flows_client()
        flow_client.get_flow(flow_id)
    except globus_sdk.GlobusAPIError as e:
        if e.http_status == 404:
            click.echo(f"Error: No flow discovered with id '{flow_id}'.", err=True)
            click.echo("Please verify that you have access to this flow.", err=True)
            click.get_current_context().exit(2)
        raise


def verify_requester_has_required_consents(
    login_manager: LoginManager, flow_id: uuid.UUID
) -> None:
    """
    Verify that the request has the proper consents to create a flow timer.

    If an additional consents are required, print instructions and exit.
    """
    flow_scope = Scope(SpecificFlowScopeBuilder(str(flow_id)).user)
    required_scope = Scope(TimersScopes.timer, dependencies=[flow_scope])

    if is_client_login():
        # Client consents don't require interactive logins.
        login_manager.add_requirement(TimersScopes.resource_server, [required_scope])
        return

    requester_id = login_manager.get_current_identity_id()
    consents = login_manager.get_auth_client().get_consents(requester_id).to_forest()

    if not consents.meets_scope_requirements(required_scope):
        click.echo(
            textwrap.dedent(
                f"""
                Warning: Flow timer creation requires additional consent.
                Please resolve with the following command, then rerun your original one:

                    globus login --timer flow:{flow_id}
                """
            )
        )
        click.get_current_context().exit(4)
