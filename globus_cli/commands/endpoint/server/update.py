import click

from globus_cli.parsing import (
    common_options, endpoint_id_arg,
    server_add_and_update_opts, server_id_arg)
from globus_cli.safeio import OutputFormatter

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('update', help='Update attributes of a Server on an Endpoint')
@common_options
@server_add_and_update_opts
@endpoint_id_arg
@server_id_arg
def server_update(endpoint_id, server_id, subject, port, scheme, hostname,
                  incoming_data_ports, outgoing_data_ports):
    """
    Executor for `globus endpoint server update`
    """
    client = get_client()

    server_doc = assemble_generic_doc(
        'server',
        subject=subject, port=port, scheme=scheme, hostname=hostname)

    # n.b. must be done after assemble_generic_doc(), as that function filters
    # out `None`s, which we need to be able to set for `'unspecified'`
    if incoming_data_ports:
        server_doc.update(incoming_data_port_start=incoming_data_ports[0],
                          incoming_data_port_end=incoming_data_ports[1])
    if outgoing_data_ports:
        server_doc.update(outgoing_data_port_start=outgoing_data_ports[0],
                          outgoing_data_port_end=outgoing_data_ports[1])

    res = client.update_endpoint_server(endpoint_id, server_id, server_doc)
    OutputFormatter(text_format=OutputFormatter.FORMAT_TEXT_RAW,
                    response_key='message').print_response(res)
