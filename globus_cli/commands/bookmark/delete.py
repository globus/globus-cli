import click

from globus_cli.parsing import common_options
from globus_cli.output_formatter import OutputFormatter

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
    OutputFormatter(text_format='text_raw', response_key='message'
                    ).print_response(res)
