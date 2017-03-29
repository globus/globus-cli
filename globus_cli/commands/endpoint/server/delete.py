import click

from globus_cli.parsing import common_options, endpoint_id_arg, server_id_arg
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client


@click.command('delete', help='Delete a server belonging to an Endpoint')
@common_options
@endpoint_id_arg
@server_id_arg
def server_delete(endpoint_id, server_id):
    """
    Executor for `globus endpoint server show`
    """
    client = get_client()
    server_doc = client.delete_endpoint_server(endpoint_id, server_id)

    formatted_print(server_doc, text_format=FORMAT_TEXT_RAW,
                    response_key='message')
