import json
import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from .._common import index_id_arg


def _print_subject(subject_doc: "globus_sdk.GlobusHTTPResponse"):
    entries = subject_doc["entries"]
    if len(entries) == 1:
        click.echo(json.dumps(entries[0], indent=2, separators=(",", ": ")))
    else:
        click.echo(json.dumps(entries, indent=2, separators=(",", ": ")))


@command("show")
@index_id_arg
@click.argument("subject")
@LoginManager.requires_login("auth", "search")
def show_command(
    *, login_manager: LoginManager, index_id: uuid.UUID, subject: str
) -> None:
    """Show the data for a given subject in an index

    This is subject the visible_to access control list on the entries for that subject.
    If there are one or more entries visible to the current user, they will be
    displayed.

    If there are no entries visible to the current user, a NotFound error will be
    raised.
    """
    search_client = login_manager.get_search_client()
    res = search_client.get_subject(index_id, subject)
    display(res, text_mode=_print_subject)
