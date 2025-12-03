from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import TUNNEL_STANDARD_FIELDS


@command("stop", short_help="Stop a tunnel.")
@click.argument("tunnel_id", metavar="TUNNEL_ID", type=click.UUID)
@LoginManager.requires_login("auth", "transfer")
def stop_tunnel_command(
    login_manager: LoginManager,
    *,
    tunnel_id: uuid.UUID,
) -> None:
    """
    Stop a tunnel but leave its data in the system.
    """
    tunnel_client = login_manager.get_transfer_client()
    data = {
        "data": {
            "type": "Tunnel",
            "attributes": {
                "state": "STOPPING",
            },
        }
    }
    res = tunnel_client.update_tunnel(str(tunnel_id), data)
    display(
        res,
        text_mode=display.RECORD,
        fields=TUNNEL_STANDARD_FIELDS,
        response_key="data",
    )
