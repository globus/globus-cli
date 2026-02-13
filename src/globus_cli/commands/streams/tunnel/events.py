from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display

TUNNEL_EVENT_LIST_FIELDS = [
    Field("Code", "attributes.code"),
    Field("Error", "attributes.is_error"),
    Field("Details", "attributes.details"),
    Field("Time", "attributes.time"),
]


@command("events", short_help="List tunnel events.")
@click.argument("tunnel_id", metavar="TUNNEL_ID", type=click.UUID)
@LoginManager.requires_login("auth", "transfer")
def events_command(
    login_manager: LoginManager,
    *,
    tunnel_id: uuid.UUID,
) -> None:
    """
    Show the events that have occurred on the tunnel.
    """
    tunnel_client = login_manager.get_transfer_client()
    res = tunnel_client.get_tunnel_events(tunnel_id)
    display(
        res,
        text_mode=display.TABLE,
        fields=TUNNEL_EVENT_LIST_FIELDS,
        response_key="data",
    )
