from __future__ import annotations

import typing as t

import click
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ColonDelimitedChoiceTuple, command
from globus_cli.termio import Field, display, formatters
from globus_cli.utils import PagingWrapper

ROLE_TYPES = (
    "flow_viewer",
    "flow_starter",
    "flow_administrator",
    "flow_owner",
    "run_manager",
    "run_monitor",
)
ORDER_BY_FIELDS = (
    "id",
    "scope_string",
    # These names are the legacy ones in the service:
    #       "created_by",
    #       "administered_by",
    # These are the new names but are not supported at time of writing:
    #       "flow_owners",
    #       "flow_administrators",
    "title",
    "created_at",
    "updated_at",
)


@command("list")
@click.option(
    "--filter-role",
    "filter_roles",
    type=click.Choice(ROLE_TYPES),
    help="Filter results by the flow's role type associated with the caller",
    multiple=True,
)
@click.option(
    "--filter-fulltext",
    type=str,
    help=(
        "Filter results based on pattern matching within a subset of fields: "
        "[id, title, subtitle, description, flow_owner, flow_administrators]"
    ),
)
@click.option(
    "--orderby",
    default=("updated_at:DESC",),
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
    filter_roles: tuple[
        t.Literal[
            "flow_viewer",
            "flow_starter",
            "flow_administrator",
            "flow_owner",
            "run_manager",
            "run_monitor",
        ],
        ...,
    ],
    orderby: tuple[
        tuple[
            t.Literal[
                "id",
                "scope_string",
                "title",
                "created_at",
                "updated_at",
            ],
            t.Literal["ASC", "DESC"],
        ],
        ...,
    ],
    filter_fulltext: str | None,
    limit: int,
) -> None:
    """
    List flows.
    """
    flows_client = login_manager.get_flows_client()
    paginator = Paginator.wrap(flows_client.list_flows)
    flow_iterator = PagingWrapper(
        paginator(
            # `filter_roles=()` results in an API error
            # the query param sent by the SDK would be `filter_roles=` (empty string)
            filter_roles=filter_roles or None,
            filter_fulltext=filter_fulltext,
            orderby=",".join(f"{field} {order}" for field, order in orderby),
        ).items(),
        json_conversion_key="flows",
        limit=limit,
    )

    fields = [
        Field("Flow ID", "id"),
        Field("Title", "title"),
        Field(
            "Owner",
            "flow_owner",
            formatter=formatters.auth.PrincipalURNFormatter(
                login_manager.get_auth_client()
            ),
        ),
        Field("Created At", "created_at", formatter=formatters.Date),
        Field("Updated At", "updated_at", formatter=formatters.Date),
    ]

    display(
        flow_iterator,
        fields=fields,
        json_converter=flow_iterator.json_converter,
    )
