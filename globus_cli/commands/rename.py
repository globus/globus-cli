import click

from globus_cli.parsing import (
    common_options, endpoint_plus_path_options,
    parse_source_and_dest_endpoint_plus_path)
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client, autoactivate


@click.command('rename', help='Rename a file or directory on an endpoint')
@common_options
@endpoint_plus_path_options(path_required=True, prefix="source")
@endpoint_plus_path_options(path_required=True, prefix="destination")
def rename_command(source_endpoint_plus_path, source_bookmark,
                   destination_endpoint_plus_path, destination_bookmark):
    """
    Executor for `globus rename`
    """
    source_ep, source_path, dest_ep, dest_path = (
        parse_source_and_dest_endpoint_plus_path(
            source_endpoint_plus_path, source_bookmark,
            destination_endpoint_plus_path, destination_bookmark))

    if source_ep != dest_ep:
        raise click.UsageError(('rename requires that the source and dest '
                                'endpoints are the same, {} != {}')
                               .format(source_ep, dest_ep))
    endpoint_id = source_ep

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    res = client.operation_rename(endpoint_id, oldpath=source_path,
                                  newpath=dest_path)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
