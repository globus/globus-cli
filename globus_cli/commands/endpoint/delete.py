import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.safeio import OutputFormatter

from globus_cli.services.transfer import get_client


@click.command('delete', help='Delete a given Endpoint')
@common_options
@endpoint_id_arg
def endpoint_delete(endpoint_id):
    """
    Executor for `globus endpoint delete`
    """
    client = get_client()
    res = client.delete_endpoint(endpoint_id)
    OutputFormatter(text_format=OutputFormatter.FORMAT_TEXT_RAW,
                    response_key='message').print_response(res)
