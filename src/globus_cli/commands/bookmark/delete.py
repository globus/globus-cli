import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from ._common import resolve_id_or_name


@command(
    "delete",
    adoc_output=(
        "When textual output is requested, the response contains a message "
        "indicating the success or failure of the operation."
    ),
    adoc_examples="""Delete a bookmark by name:

[source,bash]
----
$ globus bookmark delete "Bookmark Name"
----
""",
    short_help="Delete a bookmark",
)
@click.argument("bookmark_id_or_name")
@LoginManager.requires_login("transfer")
def bookmark_delete(*, login_manager: LoginManager, bookmark_id_or_name: str) -> None:
    """
    Delete one bookmark, given its ID or name.
    """
    transfer_client = login_manager.get_transfer_client()
    bookmark_id = resolve_id_or_name(transfer_client, bookmark_id_or_name)["id"]

    res = transfer_client.delete_bookmark(bookmark_id)
    display(res, text_mode=TextMode.text_raw, response_key="message")
