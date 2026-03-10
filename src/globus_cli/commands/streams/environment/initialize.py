from __future__ import annotations

import time
import uuid

import click
import globus_sdk
import globus_sdk.services.gcs.errors as gcserrors

from globus_cli.parsing import OMITTABLE_STRING, command

from ._common import GCSMgr, LoginMgr, TransferMgr, TunnelConf


@command("initialize", short_help="Initialize a Globus Streams environment.")
@click.argument("tunnel_id", metavar="TUNNEL_ID", type=click.UUID)
@click.argument("endpoint_id", type=click.UUID, required=False)
@click.option(
    "--cs-ttl",
    help=(
        "If the contact string was last updated more than the value of this ttl, "
        "fetch it again. In seconds"
    ),
    type=int,
    default=10,
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
@click.option(
    "--listener",
    help=(
        "This is the listener side. This is implied when "
        "--listener-contact-string is used."
    ),
    is_flag=True,
)
@click.option(
    "--force",
    help="Force an update of the LAN secret even if it exists",
    is_flag=True,
)
def initialize_command(
    tunnel_id: uuid.UUID,
    endpoint_id: uuid.UUID | None,
    listener_contact_string: str | globus_sdk.MissingType,
    cs_ttl: int,
    base_dir: str | globus_sdk.MissingType,
    listener: bool,
    force: bool,
) -> None:
    """
    Set up a local environment for use with a Globus Streams.

    User applications can connect to each other via a Globus Tunnel. One side of
    the application is the listener and the other side is the connector. There
    are helper libraries and tools that can be used by each side of the application
    to seamlessly form connections to each other through the Globus Tunnel. In order
    to get all the needed security and  configuration information to these helper
    libraries this command is used. It must be run on both the connector side
    and the again on the listener side with the --listener-contact-string option.
    """
    click.echo(f"Initializing the environment for tunnel: {tunnel_id}")

    login_mgr = LoginMgr(endpoint_id=endpoint_id)
    xfer_client = login_mgr.get_transfer_client()
    xfer_mgr = TransferMgr(tunnel_id, xfer_client)

    conf_obj = TunnelConf(tunnel_id, base_dir)

    if listener_contact_string != globus_sdk.MISSING or listener:
        listener = True
        if listener_contact_string != globus_sdk.MISSING:
            xfer_mgr.update_listener(listener_contact_string)
        stream_ap_id = xfer_mgr.get_listener_stream_id()
    else:
        contact_string = xfer_mgr.get_contact_string()
        if contact_string:
            conf_obj.connector_contact_string = contact_string
        conf_obj.connector_contact_string_ttl = cs_ttl
        stream_ap_id = xfer_mgr.get_initiator_stream_id()

    if endpoint_id is None:
        r = xfer_client.get_stream_access_point(stream_ap_id)
        endpoint_id = r["data"]["relationships"]["host_endpoint"]["data"]["id"]
        login_mgr = LoginMgr(endpoint_id=endpoint_id)

    gcs_mgr = GCSMgr(stream_ap_id, tunnel_id, login_mgr.get_gcs_client())
    if conf_obj.file_existed:
        if force:
            if not conf_obj.lankey_id:
                click.secho(
                    "WARNING: There is no lankey id in the configuration file "
                    "so we cannot delete the old key",
                    fg="yellow",
                )
            else:
                gcs_mgr.gcs_delete_lankey(uuid.UUID(conf_obj.lankey_id))
        else:
            raise Exception("Configuration exists. Use --force to overwrite it.")

    try:
        lankey, lankey_id = gcs_mgr.gcs_get_lankey(stream_ap_id)
        conf_obj.lankey = lankey
        conf_obj.lankey_id = lankey_id
    except gcserrors.GCSAPIError:
        click.secho("The LAN connection for this tunnel is not secured", fg="yellow")
        pass

    tm_now = int(time.time())
    conf_obj.tunnel_expiration_time = tm_now + xfer_mgr.get_tunnel_lifetime()
    conf_obj.endpoint_id = str(endpoint_id)
    conf_obj.update_keyfile()

    click.echo(f"The environment is initialized for use with tunnel {tunnel_id}")
    click.echo(
        f"Your application key file base directory is {conf_obj.key_file_base_dir}"
    )

    if not listener:
        click.echo(f"Your contact string is: globus.{tunnel_id}:{conf_obj.fake_port}")
