import click

from globus_cli.parsing import common_options, ENDPOINT_PLUS_REQPATH
from globus_cli.safeio import OutputFormatter

from globus_cli.services.transfer import get_client, autoactivate


@click.command('mkdir', help='Make a directory on an Endpoint')
@common_options
@click.argument('endpoint_plus_path', metavar=ENDPOINT_PLUS_REQPATH.metavar,
                type=ENDPOINT_PLUS_REQPATH)
def mkdir_command(endpoint_plus_path):
    """
    Executor for `globus mkdir`
    """
    endpoint_id, path = endpoint_plus_path

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    res = client.operation_mkdir(endpoint_id, path=path)
    formatter = OutputFormatter(response_key='message',
                                text_format=OutputFormatter.FORMAT_TEXT_RAW)
    formatter.print_response(res)
