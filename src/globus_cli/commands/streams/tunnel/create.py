from __future__ import annotations

import uuid

import click
import globus_sdk
from globus_sdk.services.transfer.data.tunnel_data import CreateTunnelData

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import OMITTABLE_INT, OMITTABLE_STRING, command
from globus_cli.termio import display

from ._common import TUNNEL_STANDARD_FIELDS


@command("create", short_help="Create a Globus tunnel.")
@click.argument(
    "initiator_stream_ap_id", metavar="INITIATOR_STREAM_AP_ID", type=click.UUID
)
@click.argument(
    "listener_stream_ap_id", metavar="LISTENER_STREAM_AP_ID", type=click.UUID
)
@click.option(
    "--label",
    type=OMITTABLE_STRING,
    default=globus_sdk.MISSING,
    help="A friendly label to associate with the tunnel.",
)
@click.option(
    "--lifetime-minutes",
    type=OMITTABLE_INT,
    default=globus_sdk.MISSING,
    help="The amount of time in minutes that the tunnel will exist.",
)
@click.option(
    "--restartable",
    is_flag=True,
    help="Indicate whether the tunnel should be restarted in the event of an error.",
)
@LoginManager.requires_login("auth", "transfer")
def create_tunnel_command(
    login_manager: LoginManager,
    *,
    initiator_stream_ap_id: uuid.UUID,
    listener_stream_ap_id: uuid.UUID,
    label: str | globus_sdk.MissingType,
    lifetime_minutes: int | globus_sdk.MissingType,
    restartable: bool,
) -> None:
    """
    Create a Globus tunnel.
    """
    data = CreateTunnelData(
        initiator_stream_ap_id,
        listener_stream_ap_id,
        label=label,
        lifetime_mins=lifetime_minutes,
        restartable=restartable,
    )
    tunnel_client = login_manager.get_transfer_client()
    res = tunnel_client.create_tunnel(data)
    display(
        res,
        text_mode=display.RECORD,
        fields=TUNNEL_STANDARD_FIELDS,
        response_key="data",
    )
