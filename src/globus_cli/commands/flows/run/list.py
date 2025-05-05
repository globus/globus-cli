from __future__ import annotations

import typing as t
import uuid

import click
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display
from globus_cli.utils import PagingWrapper

ROLE_TYPES = (
    "run_owner",
    "run_manager",
    "run_monitor",
    "flow_run_manager",
    "flow_run_monitor",
)


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
    "--filter-role",
    "filter_roles",
    type=click.Choice(ROLE_TYPES),
    help="Filter results by the run's role type associated with the caller",
    multiple=True,
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
    login_manager: LoginManager,
    *,
    limit: int,
    filter_flow_id: tuple[uuid.UUID, ...],
    filter_roles: tuple[
        t.Literal[
            "run_owner",
            "run_manager",
            "run_monitor",
            "flow_run_manager",
            "flow_run_monitor",
        ],
        ...,
    ],
) -> None:
    """
    List runs.

    Enumerates runs visible to the current user, potentially filtered by the ID of
    the flow which was used to start the run.
    """

    flows_client = login_manager.get_flows_client()

    paginator = Paginator.wrap(flows_client.list_runs)
    run_iterator = PagingWrapper(
        paginator(
            filter_flow_id=filter_flow_id,
            filter_roles=filter_roles,  # type: ignore[arg-type],
        ).items(),
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
