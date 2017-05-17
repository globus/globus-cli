import click

from globus_cli.parsing import (
    common_options, endpoint_plus_path_options, parse_endpoint_plus_path)
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client, autoactivate


@click.command('mkdir', help='Make a directory on an endpoint')
@common_options
@endpoint_plus_path_options(path_required=True)
def mkdir_command(endpoint_plus_path, bookmark):
    """
    Executor for `globus mkdir`
    """
    endpoint_id, path = parse_endpoint_plus_path(
        endpoint_plus_path, bookmark, path_required=True)

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    res = client.operation_mkdir(endpoint_id, path=path)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
