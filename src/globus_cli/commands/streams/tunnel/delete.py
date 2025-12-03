from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display


@command("delete", short_help="Delete a Globus tunnel.")
@click.argument("tunnel_id", metavar="TUNNEL_ID", type=click.UUID)
@LoginManager.requires_login("auth", "transfer")
def delete_tunnel_command(
    login_manager: LoginManager,
    *,
    tunnel_id: uuid.UUID,
) -> None:
    """
    Delete a Globus tunnel.
    """
    tunnel_client = login_manager.get_transfer_client()
    res = tunnel_client.delete_tunnel(str(tunnel_id))
    display(res, simple_text="Tunnel deleted successfully")
