import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

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
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
