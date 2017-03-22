import click

from globus_cli.safeio import safeprint
from globus_cli.parsing import common_options
from globus_cli.helpers import (
    outformat_is_json, print_json_response, is_verbose, colon_formatted_print)

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

    if outformat_is_json():
        print_json_response(res)

    # verbose output includes all fields
    elif is_verbose():
        fields = (('ID', 'id'), ('Name', 'name'),
                  ('Endpoint ID', 'endpoint_id'), ('Path', 'path'))
        colon_formatted_print(res, fields)

    # standard output is endpoint:path format
    else:
        safeprint('{}:{}'.format(res['endpoint_id'], res['path']))
