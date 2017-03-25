import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.output_formatter import OutputFormatter

from globus_cli.services.transfer import get_client


@click.command('deactivate', help='Deactivate an Endpoint')
@common_options
@endpoint_id_arg
def endpoint_deactivate(endpoint_id):
    """
    Executor for `globus endpoint deactivate`
    """
    client = get_client()
    res = client.endpoint_deactivate(endpoint_id)
    OutputFormatter(text_format='text_raw', response_key='message'
                    ).print_response(res)
