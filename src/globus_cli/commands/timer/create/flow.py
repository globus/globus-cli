from __future__ import annotations

import uuid
from datetime import datetime

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
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
    name = name or f"CLI Created Timer [{datetime.now().isoformat()}]"

    _verify_flow_exists(login_manager, flow_id)
    timers = login_manager.get_timer_client(flow_id=flow_id)

    timer_doc = globus_sdk.FlowTimer(
        flow_id=flow_id,
        name=name,
        schedule=schedule,
        body={"body": input_document.data if input_document else {}},
    )
    response = timers.create_timer(timer_doc)

    display(response["timer"], text_mode=display.RECORD, fields=CREATE_FORMAT_FIELDS)


def _verify_flow_exists(login_manager: LoginManager, flow_id: uuid.UUID) -> None:
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
