import click

from globus_cli.safeio import safeprint
from globus_cli.parsing import (
    common_options, endpoint_id_arg, endpoint_create_and_update_params,
    endpoint_create_and_update_validate_params)
from globus_cli.helpers import outformat_is_json, print_json_response

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('update', help='Update attributes of an Endpoint')
@common_options
@endpoint_id_arg
@endpoint_create_and_update_params(create=False)
def endpoint_update(endpoint_id, display_name, description, organization,
                    department, keywords, contact_email, contact_info,
                    info_link, public, default_directory, force_encryption,
                    oauth_server, myproxy_server, myproxy_dn, network_use,
                    custom_concurrency, custom_parallelism, location_automatic,
                    location, disable_verify):
    """
    Executor for `globus endpoint update`
    """
    # validate/parse args
    validated = endpoint_create_and_update_validate_params(
        network_use, custom_concurrency, custom_parallelism, location,
        location_automatic)
    (max_concurrency, preferred_concurrency,
     max_parallelism, preferred_parallelism, location_value) = validated

    ep_doc = assemble_generic_doc(
        'endpoint',
        display_name=display_name, description=description,
        organization=organization, department=department, keywords=keywords,
        contact_email=contact_email, contact_info=contact_info,
        info_link=info_link, force_encryption=force_encryption, public=public,
        default_directory=default_directory, myproxy_server=myproxy_server,
        myproxy_dn=myproxy_dn, oauth_server=oauth_server,
        network_use=network_use, max_concurrency=max_concurrency,
        preferred_concurrency=preferred_concurrency,
        max_parallelism=max_parallelism,
        preferred_parallelism=preferred_parallelism,
        disable_verify=disable_verify, location=location_value)

    client = get_client()
    res = client.update_endpoint(endpoint_id, ep_doc)

    if outformat_is_json():
        print_json_response(res)
    else:
        safeprint(res['message'])
