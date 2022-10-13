from __future__ import annotations

import click

from globus_cli.commands.flows._common import FLOW_SUMMARY_FORMAT_FIELDS
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import formatted_print
from globus_cli.utils import PagingWrapper

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("list", short_help="List flows")
@click.option(
    "--filter-role",
    type=click.Choice(ROLE_TYPES),
    help="Filter results by the flow's role type associated with the caller",
)
@click.option(
    "--filter-fulltext",
    type=str,
    help="Filter results based on pattern matching within a subset of fields: "
    "[id, title, subtitle, description, flow_owner, flow_administrators]",
)
@click.option(
    "--limit",
    default=25,
    show_default=True,
    metavar="N",
    type=click.IntRange(1),
    help="The maximum number of results to return.",
)
@LoginManager.requires_login(LoginManager.FLOWS_RS)
def list_command(
    login_manager: LoginManager,
    filter_role: str | None,
    filter_fulltext: str | None,
    limit: int,
):
    """
    List flows
    """
    flows_client = login_manager.get_flows_client()
    flow_iterator = PagingWrapper(
        flows_client.paginated.list_flows(
            filter_role=filter_role,
            filter_fulltext=filter_fulltext,
            orderby="updated_at DESC",
        ).items(),
        json_conversion_key="flows",
        limit=limit,
    )

    formatted_print(
        flow_iterator,
        fields=FLOW_SUMMARY_FORMAT_FIELDS,
        json_converter=flow_iterator.json_converter,
    )
