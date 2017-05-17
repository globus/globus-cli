import click

from globus_cli.parsing import common_options
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW
from globus_cli.services.transfer import get_client
from globus_cli.helpers import resolve_bookmark_id_or_name


@click.command('delete', help='Delete a bookmark')
@common_options
@click.argument('bookmark_id_or_name')
def bookmark_delete(bookmark_id_or_name):
    """
    Executor for `globus bookmark delete`
    """
    client = get_client()
    bookmark_id = resolve_bookmark_id_or_name(bookmark_id_or_name)["id"]

    res = client.delete_bookmark(bookmark_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
