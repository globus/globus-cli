from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import OMITTABLE_STRING, command
from globus_cli.termio import display

from ._common import TUNNEL_STANDARD_FIELDS


@command("update", short_help="Update a Globus tunnel.")
@click.argument("tunnel_id", metavar="TUNNEL_ID", type=click.UUID)
@click.option(
    "--label",
    type=OMITTABLE_STRING,
    default=globus_sdk.MISSING,
    help="A friendly label to associate with the tunnel.",
)
@LoginManager.requires_login("auth", "transfer")
def update_tunnel_command(
    login_manager: LoginManager,
    *,
    tunnel_id: uuid.UUID,
    label: str | globus_sdk.MissingType,
) -> None:
    """
    Update a Globus tunnel.
    """
    tunnel_client = login_manager.get_transfer_client()
    data = {
        "data": {
            "type": "Tunnel",
            "attributes": {
                "label": label,
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
