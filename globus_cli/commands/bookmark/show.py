import click

from globus_cli.parsing import common_options
from globus_cli.safeio import OutputFormatter
from globus_cli.helpers import is_verbose

from globus_cli.services.transfer import get_client
from globus_cli.commands.bookmark.helpers import resolve_id_or_name


@click.command(
    'show', help=("Given a bookmark name or ID resolves bookmark in endpoint:"
                  "path format. Use --verbose for additional fields."))
@common_options
@click.argument('bookmark_id_or_name')
def bookmark_show(bookmark_id_or_name):
    """
    Executor for `globus bookmark show`
    """
    client = get_client()
    res = resolve_id_or_name(client, bookmark_id_or_name)
    OutputFormatter(text_format=OutputFormatter.FORMAT_TEXT_RECORD
                    ).print_response(
        res, simple_text=(
            # standard output is endpoint:path format
            '{}:{}'.format(res['endpoint_id'], res['path'])
            # verbose output includes all fields
            if not is_verbose() else None))
