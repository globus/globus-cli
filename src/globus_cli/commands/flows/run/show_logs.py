from __future__ import annotations

import json
import uuid

import click
from globus_sdk.paging import Paginator

from globus_cli.commands.flows._common import FlowScopeInjector
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, run_id_arg
from globus_cli.termio import Field, display, print_command_hint
from globus_cli.utils import PagingWrapper


@command("show-logs")
@run_id_arg
@click.option(
    "--details",
    help="Include log entry details (using a text record format).",
    is_flag=True,
)
@click.option(
    "--reverse",
    help="Reverse the order of the results.",
    is_flag=True,
)
@click.option(
    "--limit",
    default=100,
    show_default=True,
    metavar="N",
    type=click.IntRange(1),
    help="The maximum number of results to return.",
)
@LoginManager.requires_login("flows")
def show_logs_command(
    login_manager: LoginManager,
    *,
    run_id: uuid.UUID,
    details: bool,
    reverse: bool,
    limit: int,
) -> None:
    """
    List run logs entries.

    Enumerates the run log entries for a given run.
    """

    flows_client = login_manager.get_flows_client()
    flow_scope_injector = FlowScopeInjector(login_manager)

    # get the Flow, to check INACTIVE status below
    with flow_scope_injector.for_run(run_id):
        run_doc = flows_client.get_run(run_id)

    def wrapped_get_run_logs(*args, **kwargs):  # type:ignore[no-untyped-def]
        """Thin wrapper to inject flow scope into paginated get_run_logs calls."""
        with flow_scope_injector.for_run(run_id):
            return flows_client.get_run_logs(*args, **kwargs)

    paginator = Paginator.wrap(wrapped_get_run_logs)
    entry_iterator = PagingWrapper(
        paginator(run_id=run_id, reverse_order=reverse).items(),
        limit=limit,
        json_conversion_key="entries",
    )

    fields = [
        Field("Time", "time"),
        Field("Code", "code"),
        Field("Description", "description"),
    ]

    if details:
        # Display the log entries, including the details field, in text record format.
        fields.append(Field("Details", "details"))
        entry_list = list(entry_iterator)
        for entry in entry_list:
            entry["details"] = json.dumps(entry["details"])

        display(entry_list, text_mode=display.RECORD_LIST, fields=fields)
    else:
        print_command_hint(
            "Displaying summary data. "
            "To see details of each event, use the --details option.\n"
        )
        # Display the log entries in a table.
        display(
            entry_iterator, fields=fields, json_converter=entry_iterator.json_converter
        )

    if run_doc["status"] == "INACTIVE":
        print_command_hint(
            (
                "\nNOTE: This run is INACTIVE. "
                "No further logs will be added until it is resumed."
            ),
            color="bright_blue",
        )

    # Check if there are more results
    if entry_iterator.has_next():
        print_command_hint(
            f"\nResults hidden by the current limit of {limit}. "
            "To see more events, set the --limit option to a higher value."
        )
