from __future__ import annotations

import click

from globus_cli.commands.flows._common import FLOW_SUMMARY_FORMAT_FIELDS
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import formatted_print

ROLE_TYPES = ("flow_viewer", "flow_starter", "flow_administrator", "flow_owner")


@command("list", short_help="List flows")
@click.option(
    "--filter-role",
    required=False,
    type=click.Choice(ROLE_TYPES),
    help="Filter results by the flow's role type associated with the caller",
)
@click.option(
    "--filter-fulltext",
    required=False,
    type=str,
    help="Filter results based on pattern matching within a subset of fields: "
    "[id, title, subtitle, description, flow_owner, flow_administrators]",
)
@LoginManager.requires_login(LoginManager.FLOWS_RS)
def list_command(
    login_manager: LoginManager,
    filter_role: str | None,
    filter_fulltext: str | None,
):
    """
    List flows
    """
    flows_client = login_manager.get_flows_client()
    # TODO: paginate once path supports pagination
    #  https://app.shortcut.com/globus/story/18445/add-pagination-back-to-flowsclient-flow-list
    response = flows_client.list_flows(
        filter_role=filter_role,
        filter_fulltext=filter_fulltext,
        query_params={"orderby": "updated_at DESC"},
    )
    formatted_print(
        response["flows"],
        fields=FLOW_SUMMARY_FORMAT_FIELDS,
    )
