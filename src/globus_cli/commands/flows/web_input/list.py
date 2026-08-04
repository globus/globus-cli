from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ColonDelimitedChoiceTuple, command
from globus_cli.termio import Field, display
from globus_cli.utils import PagingWrapper

ROLE_TYPES = ("viewer", "respondent")
STATE_TYPES = ("open", "closed")
ORDER_BY_FIELDS = ("created_timestamp", "edited_timestamp", "closed_timestamp")


@command("list")
@click.option(
    "--filter-role",
    "filter_roles",
    type=click.Choice(ROLE_TYPES),
    help="Filter results by the caller's role on the web input",
    multiple=True,
)
@click.option(
    "--filter-state",
    "filter_states",
    type=click.Choice(STATE_TYPES),
    help="Filter results by the web input's state",
    multiple=True,
)
@click.option(
    "--filter-flow-id",
    "filter_flow_ids",
    help=(
        "Filter results to web inputs with a particular flow ID or flow IDs. "
        "This option may be specified multiple times to filter by multiple "
        "flow IDs."
    ),
    multiple=True,
    type=click.UUID,
)
@click.option(
    "--filter-run-id",
    "filter_run_ids",
    help=(
        "Filter results to web inputs with a particular run ID or run IDs. "
        "This option may be specified multiple times to filter by multiple "
        "run IDs."
    ),
    multiple=True,
    type=click.UUID,
)
@click.option(
    "--orderby",
    default=("created_timestamp:DESC",),
    show_default=True,
    type=ColonDelimitedChoiceTuple(
        choices=tuple(
            f"{field}:{order}" for field in ORDER_BY_FIELDS for order in ("ASC", "DESC")
        ),
        case_sensitive=False,
    ),
    multiple=True,
    metavar=f"[{'|'.join(ORDER_BY_FIELDS)}]:[ASC|DESC]",
    help="""
        Sort results by the given field and ordering.
        ASC for ascending, DESC for descending.

        This option can be specified multiple times to sort by multiple fields.
    """,
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
    filter_roles: tuple[t.Literal["viewer", "respondent"], ...],
    filter_states: tuple[t.Literal["open", "closed"], ...],
    filter_flow_ids: tuple[uuid.UUID, ...],
    filter_run_ids: tuple[uuid.UUID, ...],
    orderby: tuple[
        tuple[
            t.Literal["created_timestamp", "edited_timestamp", "closed_timestamp"],
            t.Literal["ASC", "DESC"],
        ],
        ...,
    ],
    limit: int,
) -> None:
    """
    List web inputs accessible to the current user.
    """
    flows_client = login_manager.get_flows_client()

    paginator = Paginator.wrap(flows_client.list_web_inputs)
    web_input_iterator = PagingWrapper(
        paginator(
            filter_roles=filter_roles or globus_sdk.MISSING,
            filter_states=filter_states or globus_sdk.MISSING,
            filter_flow_ids=filter_flow_ids or globus_sdk.MISSING,
            filter_run_ids=filter_run_ids or globus_sdk.MISSING,
            orderby=",".join(f"{field} {order}" for field, order in orderby),
        ).items(),
        json_conversion_key="web_input_summaries",
        limit=limit,
    )

    fields = [
        Field("Web Input ID", "id"),
        Field("Status", "status"),
        Field("Input Type", "input_type"),
        Field("Title", "title"),
        Field("Flow Title", "flow.title"),
        Field("Run Label", "run.label"),
    ]

    display(
        web_input_iterator,
        fields=fields,
        json_converter=web_input_iterator.json_converter,
    )
