from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.parsing import OMITTABLE_INT, OMITTABLE_STRING

from . import _common as gt_utils


@click.command(name="update")
@click.argument("tunnel_id", type=click.UUID)
@click.option(
    "--cs-ttl",
    help=(
        "If the contact string was last updated more than the value of this ttl,"
        "fetch it again"
    ),
    type=OMITTABLE_INT,
    default=globus_sdk.MISSING,
)
@click.option(
    "--base-dir",
    help=(
        "The directory that stores configuration information "
        "(default: ~/.globus/tunnels)"
    ),
    type=OMITTABLE_STRING,
    default=globus_sdk.MISSING,
)
@click.option(
    "--listener-contact-string",
    help="When initializing an application listener provide its contact string",
    type=OMITTABLE_STRING,
    default=globus_sdk.MISSING,
)
def update_command(
    tunnel_id: uuid.UUID,
    listener_contact_string: str | globus_sdk.MissingType,
    cs_ttl: int | globus_sdk.MissingType,
    base_dir: str | globus_sdk.MissingType,
) -> None:
    """Update the Globus Tunnel information in the local environment.

    This command is used to update the login tokens, contact string,
    or application listener string in the local environment. It does
    not update the lan secret.
    """

    click.echo(f"Updating the environment for tunnel: {tunnel_id}")

    conf_obj = gt_utils.TunnelConf(tunnel_id, base_dir)
    if not conf_obj.file_existed:
        raise FileNotFoundError(
            f"The file {conf_obj.keyfile} was not found. Initialize the "
            "environment first."
        )

    login_mgr = gt_utils.LoginMgr()
    xfer_client = login_mgr.get_transfer_client()
    xfer_mgr = gt_utils.TransferMgr(tunnel_id, xfer_client)

    if listener_contact_string != globus_sdk.MISSING:
        click.echo(
            "Updating the application listener on the Tunnel: "
            f"{tunnel_id} to: {listener_contact_string}"
        )
        xfer_mgr.update_listener(listener_contact_string)
    else:
        cs = xfer_mgr.get_contact_string()
        if cs:
            conf_obj.connector_contact_string = cs
        if cs_ttl is not None:
            conf_obj.connector_contact_string_ttl = cs_ttl
        conf_obj.update_keyfile()
