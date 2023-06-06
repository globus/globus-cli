from __future__ import annotations

import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command, local_user_option
from globus_cli.termio import TextMode, display


@command(
    "mkdir",
    short_help="Create a directory on an endpoint",
    adoc_examples="""Create a directory under your home directory:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ mkdir ep_id:~/testfolder
----
""",
)
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_REQPATH)
@local_user_option
@LoginManager.requires_login("transfer")
def mkdir_command(
    *,
    login_manager: LoginManager,
    endpoint_plus_path: tuple[uuid.UUID, str],
    local_user: str | None,
):
    """Make a directory on an endpoint at the given path.

    {AUTOMATIC_ACTIVATION}
    """
    from globus_cli.services.transfer import autoactivate

    endpoint_id, path = endpoint_plus_path

    transfer_client = login_manager.get_transfer_client()
    autoactivate(transfer_client, endpoint_id, if_expires_in=60)

    res = transfer_client.operation_mkdir(endpoint_id, path=path, local_user=local_user)
    display(res, text_mode=TextMode.text_raw, response_key="message")
