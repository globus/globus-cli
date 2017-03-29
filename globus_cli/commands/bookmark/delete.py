import click

from globus_cli.parsing import common_options
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client


@click.command('delete', help='Delete a Bookmark')
@common_options
@click.argument('bookmark_id')
def bookmark_delete(bookmark_id):
    """
    Executor for `globus bookmark delete`
    """
    client = get_client()

    res = client.delete_bookmark(bookmark_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
