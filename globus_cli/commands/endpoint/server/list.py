from textwrap import dedent
import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.output_formatter import OutputFormatter
from globus_cli.services.transfer import (display_name_or_cname, get_client)


@click.command('list', help='List all servers belonging to an Endpoint')
@common_options
@endpoint_id_arg
def server_list(endpoint_id):
    """
    Executor for `globus endpoint server list`
    """
    client = get_client()

    endpoint = client.get_endpoint(endpoint_id)

    if endpoint['host_endpoint_id']:  # not GCS -- this is a share endpoint
        raise click.UsageError(dedent("""\
            {id} ({0}) is a share and does not have servers.

            To see details of the share, use
                globus endpoint show {id}

            To list the servers on the share's host endpoint, use
                globus endpoint server list {host_endpoint_id}
        """).format(display_name_or_cname(endpoint), **endpoint.data))

    if endpoint['s3_url']:  # not GCS -- this is an S3 endpoint
        res = {'s3_url': endpoint['s3_url']}
        fields = [("S3 URL", 's3_url')]
        text_format = 'text_record'
    else:
        # regular GCS host endpoint; use Transfer's server list API
        res = client.endpoint_server_list(endpoint_id)
        fields = (('ID', 'id'),
                  ('URI', lambda s: (s['uri'] or
                                     "none (Globus Connect Personal)")))
        text_format = 'text_table'
    OutputFormatter(text_format=text_format, fields=fields).print_response(res)
