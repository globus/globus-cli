from __future__ import annotations

import glob
import os
import sys
import time
import uuid

import click

from ._common import TunnelConf


def clean_one(tunnel_id: uuid.UUID, force: bool, base_dir: str, tm_now: int) -> bool:
    conf_obj = TunnelConf(tunnel_id, base_dir)
    if not conf_obj.file_existed:
        click.echo(f"The tunnel {tunnel_id} does not exist")
        return False

    if (
        conf_obj.tunnel_expiration_time is None
        or conf_obj.tunnel_expiration_time < tm_now
        or force
    ):
        # we should probably have a prompt
        click.echo(f"Deleting the tunnel configuration {tunnel_id}")
        os.remove(conf_obj.keyfile)
        return True
    else:
        click.echo(f"The tunnel {tunnel_id} is not expired")
        return False


@click.command(name="cleanup")
@click.argument("tunnel_id", type=click.UUID, required=False)
@click.option(
    "--force",
    help="Force a delete even if the tunnel is not expired",
    type=bool,
    is_flag=True,
)
@click.option(
    "--all",
    help="Look at every tunnel configuration file and delete them if expired",
    type=bool,
    is_flag=True,
)
@click.option(
    "--base-dir",
    help=(
        "The directory that stores configuration information "
        "(default: ~/.globus/tunnels)"
    ),
    type=str,
    default="~/.globus/tunnels",
)
def cleanup_command(
    tunnel_id: uuid.UUID | None, force: bool, all: bool, base_dir: str
) -> None:
    """Cleanup Tunnel configuration files.

    This command will simply delete the information created on a local system
    with the initialize command.
    """
    tm_now = int(time.time())
    if all and force:
        if not click.confirm(
            "This will delete all your tunnel configurations even if they are not "
            "expired, are you sure?"
        ):
            return

    base_dir = os.path.expanduser(base_dir)
    if not all:
        if tunnel_id is None:
            click.echo("You must provide a tunnel id if not using --all")
            sys.exit(1)
        deleted = clean_one(tunnel_id, force, base_dir, tm_now)
        if not deleted:
            sys.exit(2)
    else:
        pattern = os.path.join(base_dir, "*.conf")
        for filepath in glob.glob(pattern):
            filepath = os.path.basename(filepath)
            tid = filepath[:-5]
            clean_one(uuid.UUID(tid), force, base_dir, tm_now)
