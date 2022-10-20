import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import FORMAT_TEXT_RECORD, Field, formatted_print, is_verbose

from ._common import resolve_id_or_name


@command(
    "show",
    adoc_output="""
When textual output is requested, the output varies depending on verbosity.

By default, output is simply 'ENDPOINT_ID:PATH'

If *-v* or *--verbose* is given, output has the following fields:

- 'ID'
- 'Name'
- 'Endpoint ID'
- 'Path'
""",
    adoc_examples="""Resolve a bookmark, for use in another command:

[source,bash]
----
$ globus ls "$(globus bookmark show BOOKMARK_NAME)"
----
""",
    short_help="Resolve a bookmark name or ID to an endpoint:path",
)
@click.argument("bookmark_id_or_name")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def bookmark_show(*, login_manager: LoginManager, bookmark_id_or_name):
    """
    Given a single bookmark ID or bookmark name, show the bookmark details. By default,
    when the format is TEXT, this will display the endpoint ID and path in
    'ENDPOINT_ID:PATH' notation.

    The default output is suitable for use in a subshell in another command.

    If *-v, --verbose* is given, several fields will be displayed.
    """
    transfer_client = login_manager.get_transfer_client()
    res = resolve_id_or_name(transfer_client, bookmark_id_or_name)
    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=[
            Field("ID", "id"),
            Field("Name", "name"),
            Field("Endpoint ID", "endpoint_id"),
            Field("Path", "path"),
        ],
        simple_text=(
            # standard output is endpoint:path format
            "{}:{}".format(res["endpoint_id"], res["path"])
            # verbose output includes all fields
            if not is_verbose()
            else None
        ),
    )
