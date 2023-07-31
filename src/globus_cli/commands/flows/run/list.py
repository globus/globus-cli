from __future__ import annotations

import uuid

import click
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display
from globus_cli.utils import PagingWrapper


@command("list")
@click.option(
    "--filter-flow-id",
    help=(
        "Filter results to runs with a particular flow ID or flow IDs. "
        "This option may be specified multiple times to filter by multiple "
        "flow IDs."
    ),
    multiple=True,
    type=click.UUID,
)
@click.option(
    "--limit",
    default=25,
    show_default=True,
    metavar="N",
    type=click.IntRange(1),
    help="The maximum number of results to return.",
)
@LoginManager.requires_login("flows")
def list_command(
    login_manager: LoginManager, *, limit: int, filter_flow_id: tuple[uuid.UUID, ...]
) -> None:
    """
    List runs

    Enumerates runs visible to the current user, potentially filtered by the ID of
    the flow which was used to start the run.
    """

    flows_client = login_manager.get_flows_client()

    paginator = Paginator.wrap(flows_client.list_runs)
    run_iterator = PagingWrapper(
        paginator(filter_flow_id=filter_flow_id).items(),
        json_conversion_key="runs",
        limit=limit,
    )

    fields = [
        Field("Run ID", "run_id"),
        Field("Flow Title", "flow_title"),
        Field("Run Label", "label"),
        Field("Status", "status"),
    ]

    display(run_iterator, fields=fields, json_converter=run_iterator.json_converter)
