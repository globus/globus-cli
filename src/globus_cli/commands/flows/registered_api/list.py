from __future__ import annotations

import typing as t

import click
import globus_sdk
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ColonDelimitedChoiceTuple, command
from globus_cli.termio import Field, display, formatters
from globus_cli.utils import PagingWrapper

ROLE_TYPES = ("owner", "administrator", "viewer")
ORDER_BY_FIELDS = ("id", "name", "created_timestamp", "updated_timestamp")


@command("list")
@click.option(
    "--filter-role",
    "filter_roles",
    type=click.Choice(ROLE_TYPES),
    help="Filter results by the registered API's role type associated with the caller",
    multiple=True,
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
    filter_roles: tuple[t.Literal["owner", "administrator", "viewer"], ...],
    orderby: tuple[
        tuple[
            t.Literal["id", "name", "created_timestamp", "updated_timestamp"],
            t.Literal["ASC", "DESC"],
        ],
        ...,
    ],
    limit: int,
) -> None:
    """
    List registered APIs.
    """
    flows_client = login_manager.get_flows_client()
    paginator = Paginator.wrap(flows_client.list_registered_apis)
    api_iterator = PagingWrapper(
        paginator(
            filter_roles=filter_roles or globus_sdk.MISSING,
            orderby=",".join(f"{field} {order}" for field, order in orderby),
        ).items(),
        json_conversion_key="registered_apis",
        limit=limit,
    )

    fields = [
        Field("Registered API ID", "id"),
        Field("Name", "name"),
        Field("Created At", "created_timestamp", formatter=formatters.Date),
        Field("Updated At", "updated_timestamp", formatter=formatters.Date),
    ]

    display(
        api_iterator,
        fields=fields,
        json_converter=api_iterator.json_converter,
    )
