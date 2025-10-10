from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command, local_user_option
from globus_cli.termio import display


@command(
    "mkdir",
    short_help="Create a directory on an endpoint.",
    adoc_examples="""Create a directory under your home directory:

[source,bash]
----
$ ep_id=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ mkdir ep_id:~/testfolder
----
""",
)
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_REQPATH)
@local_user_option
@LoginManager.requires_login("transfer")
def mkdir_command(
    login_manager: LoginManager,
    *,
    endpoint_plus_path: tuple[uuid.UUID, str],
    local_user: str | globus_sdk.MissingType,
) -> None:
    """Make a directory on an endpoint at the given path."""
    endpoint_id, path = endpoint_plus_path
    transfer_client = login_manager.get_transfer_client()

    res = transfer_client.operation_mkdir(endpoint_id, path=path, local_user=local_user)
    display(res, text_mode=display.RAW, response_key="message")
