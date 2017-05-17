import click

from globus_cli.parsing import common_options
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RECORD
from globus_cli.helpers import is_verbose

from globus_cli.helpers import resolve_bookmark_id_or_name


@click.command(
    'show', help=("Given a bookmark name or ID resolves bookmark in endpoint:"
                  "path format. Use --verbose for additional fields."))
@common_options
@click.argument('bookmark_id_or_name')
def bookmark_show(bookmark_id_or_name):
    """
    Executor for `globus bookmark show`
    """
    res = resolve_bookmark_id_or_name(bookmark_id_or_name)
    formatted_print(
        res, text_format=FORMAT_TEXT_RECORD,
        fields=(('ID', 'id'), ('Name', 'name'),
                ('Endpoint ID', 'endpoint_id'), ('Path', 'path')),
        simple_text=(
            # standard output is endpoint:path format
            '{}:{}'.format(res['endpoint_id'], res['path'])
            # verbose output includes all fields
            if not is_verbose() else None))
