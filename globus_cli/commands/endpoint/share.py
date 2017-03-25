import click

from globus_cli.parsing import (
    common_options, endpoint_create_and_update_params, ENDPOINT_PLUS_REQPATH)
from globus_cli.output_formatter import OutputFormatter
from globus_cli.services.transfer import (
    autoactivate, get_client, assemble_generic_doc)


@click.command('share', help='Create a new Share, hosted on an Endpoint')
@common_options
@click.argument('endpoint_plus_path', metavar='HOST_ENDPOINT_ID:HOST_PATH',
                type=ENDPOINT_PLUS_REQPATH)
@endpoint_create_and_update_params(create=True, shared_ep=True)
def endpoint_create_share(endpoint_plus_path, display_name, description,
                          department, keywords, organization, contact_email,
                          contact_info, info_link):
    """
    Executor for `globus share create`
    """
    endpoint_id, host_path = endpoint_plus_path

    ep_doc = assemble_generic_doc(
        'shared_endpoint',
        host_endpoint=endpoint_id, host_path=host_path,
        display_name=display_name, description=description,
        department=department, keywords=keywords, organization=organization,
        contact_email=contact_email, contact_info=contact_info,
        info_link=info_link, public=True)

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)
    res = client.create_shared_endpoint(ep_doc)

    OutputFormatter(text_format='text_record',
                    fields=[('Message', 'message'), ('Endpoint ID', 'id')]
                    ).print_response(res)
