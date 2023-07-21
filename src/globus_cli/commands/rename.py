from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg, local_user_option
from globus_cli.termio import TextMode, display


@command(
    "rename",
    short_help="Rename a file or directory on an endpoint",
    adoc_examples="""Rename a directory:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus rename $ep_id:~/tempdir $ep_id:~/project-foo
----
""",
)
@endpoint_id_arg
@click.argument("source", metavar="SOURCE_PATH")
@click.argument("destination", metavar="DEST_PATH")
@local_user_option
@LoginManager.requires_login("transfer")
def rename_command(
    login_manager: LoginManager,
    *,
    endpoint_id: uuid.UUID,
    source: str,
    destination: str,
    local_user: str | None,
):
    """Rename a file or directory on an endpoint.

    The old path must be an existing file or directory. The new path must not yet
    exist.

    The new path does not have to be in the same directory as the old path, but
    most endpoints will require it to stay on the same filesystem.
    """
    from globus_cli.services.transfer import autoactivate

    transfer_client = login_manager.get_transfer_client()
    autoactivate(transfer_client, endpoint_id, if_expires_in=60)

    res = transfer_client.operation_rename(
        endpoint_id, oldpath=source, newpath=destination, local_user=local_user
    )
    display(res, text_mode=TextMode.text_raw, response_key="message")
