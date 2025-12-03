from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import TUNNEL_STANDARD_FIELDS


@command("show", short_help="Show the attributes of a tunnel.")
@click.argument("tunnel_id", metavar="TUNNEL_ID", type=click.UUID)
@LoginManager.requires_login("auth", "transfer")
def show_tunnel_command(
    login_manager: LoginManager,
    *,
    tunnel_id: uuid.UUID,
) -> None:
    """
    Show the attributes of a Globus tunnel.
    """
    tunnel_client = login_manager.get_transfer_client()
    res = tunnel_client.get_tunnel(str(tunnel_id))
    display(
        res,
        text_mode=display.RECORD,
        fields=TUNNEL_STANDARD_FIELDS,
        response_key="data",
    )
