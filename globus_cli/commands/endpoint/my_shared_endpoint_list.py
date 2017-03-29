import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.safeio import formatted_print

from globus_cli.services.transfer import (
    ENDPOINT_LIST_FIELDS, get_client)


@click.command(
    'my-shared-endpoint-list',
    help='List all Shared Endpoints on an Endpoint by the current user')
@common_options
@endpoint_id_arg
def my_shared_endpoint_list(endpoint_id):
    """
    Executor for `globus endpoint my-shared-endpoint-list`
    """
    client = get_client()
    ep_iterator = client.my_shared_endpoint_list(endpoint_id)

    formatted_print(ep_iterator, fields=ENDPOINT_LIST_FIELDS)
