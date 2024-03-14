from __future__ import annotations

import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command, local_user_option
from globus_cli.termio import Field, display

STAT_FIELDS = [
    Field("Name", "name"),
    Field("Type", "type"),
    Field("Last Modified", "last_modified"),
    Field("Size", "size"),
    Field("Permissions", "permissions"),
    Field("User", "user"),
    Field("Group", "group"),
]


@command(
    "stat",
    short_help="Get the status of a path",
    adoc_examples=r"""Get the status of a path on a collection.

[source,bash]
----
$ col_id=6c54cade-bde5-45c1-bdea-f4bd71dba2cc
$ globus stat $col_id:/home/share/godata/file1.txt
----

""",
)
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_REQPATH)
@local_user_option
@LoginManager.requires_login("transfer")
def stat_command(
    login_manager: LoginManager,
    *,
    endpoint_plus_path: tuple[uuid.UUID, str],
    local_user: str | None,
) -> None:
    """
    Get the status of a path on a collection.
    """
    transfer_client = login_manager.get_transfer_client()
    endpoint_id, path = endpoint_plus_path

    try:
        res = transfer_client.operation_stat(endpoint_id, path, local_user=local_user)
        display(
            res,
            text_mode=display.RECORD,
            fields=STAT_FIELDS,
        )

    except globus_sdk.TransferAPIError as error:
        if error.code == "NotFound":
            display(error.raw_json, simple_text=f"Nothing found at {path}")
        else:
            raise
