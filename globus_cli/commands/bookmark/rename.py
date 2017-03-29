import click

from globus_cli.parsing import common_options
from globus_cli.safeio import formatted_print

from globus_cli.services.transfer import get_client


@click.command('rename', help='Change a Bookmark\'s name')
@common_options
@click.argument('bookmark_id')
@click.argument('new_bookmark_name')
def bookmark_rename(bookmark_id, new_bookmark_name):
    """
    Executor for `globus bookmark rename`
    """
    client = get_client()

    submit_data = {
        'name': new_bookmark_name
    }

    res = client.update_bookmark(bookmark_id, submit_data)
    formatted_print(res, simple_text='Success')
