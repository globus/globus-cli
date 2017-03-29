import click

from globus_cli.parsing import (
    common_options, endpoint_id_arg, endpoint_create_and_update_params)
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('update', help='Update attributes of an Endpoint')
@common_options
@endpoint_id_arg
@endpoint_create_and_update_params(create=False)
def endpoint_update(endpoint_id, display_name, description, organization,
                    department, keywords, contact_email, contact_info,
                    info_link, public, default_directory, force_encryption,
                    oauth_server, myproxy_server, myproxy_dn):
    """
    Executor for `globus endpoint update`
    """
    client = get_client()

    ep_doc = assemble_generic_doc(
        'endpoint',
        display_name=display_name, description=description,
        organization=organization, department=department, keywords=keywords,
        contact_email=contact_email, contact_info=contact_info,
        info_link=info_link, force_encryption=force_encryption, public=public,
        default_directory=default_directory, myproxy_server=myproxy_server,
        myproxy_dn=myproxy_dn, oauth_server=oauth_server)

    res = client.update_endpoint(endpoint_id, ep_doc)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
