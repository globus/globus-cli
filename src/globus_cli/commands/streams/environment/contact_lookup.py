from __future__ import annotations

import time
import uuid

import click
import globus_sdk

from globus_cli.parsing import OMITTABLE_STRING

from . import _common as gt_utils


@click.command(name="contact-lookup")
@click.argument("tunnel_id", type=click.UUID)
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
    "--skip-update",
    help=(
        "Do not attempt to fetch a new contact string from Globus Transfer. In this "
        "case an expired cached contact string could be returned."
    ),
    type=bool,
    is_flag=True,
)
def contact_lookup(
    tunnel_id: uuid.UUID, base_dir: str | globus_sdk.MissingType, skip_update: bool
) -> None:
    """Lookup a Globus Tunnel ID in the local environment.

    This command is largely used by the Globus Tunnel helper libraries
    and applications, however it can be run directly. If the contact string
    associated with the Tunnel has expired this tool will form a connection
    zwith Globus Transfer in order to fetch a new one.
    """
    conf_obj = gt_utils.TunnelConf(tunnel_id, base_dir)
    if not conf_obj.file_existed:
        raise Exception(
            f"The environment is not configured for the Globus Tunnel {tunnel_id}"
        )

    tm_now = int(time.time())
    if (
        conf_obj.connector_contact_string is None
        or tm_now > conf_obj.update_time + conf_obj.connector_contact_string_ttl
    ) and not skip_update:
        login_mgr = gt_utils.LoginMgr()
        xfer_client = login_mgr.get_transfer_client()
        xfer_mgr = gt_utils.TransferMgr(tunnel_id, xfer_client)
        conf_obj.connector_contact_string = xfer_mgr.get_contact_string()
        conf_obj.update_keyfile()

    print(conf_obj.dumps())
