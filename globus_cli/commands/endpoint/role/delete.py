import click

from globus_cli.parsing import common_options, endpoint_id_arg, role_id_arg
from globus_cli.output_formatter import OutputFormatter

from globus_cli.services.transfer import get_client


@click.command('delete', help='Remove a Role from an Endpoint')
@common_options
@endpoint_id_arg
@role_id_arg
def role_delete(role_id, endpoint_id):
    """
    Executor for `globus endpoint role delete`
    """
    client = get_client()
    res = client.delete_endpoint_role(endpoint_id, role_id)
    OutputFormatter(text_format='text_raw', response_key='message'
                    ).print_response(res)
