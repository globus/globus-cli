import click

from globus_cli.safeio import safeprint
from globus_cli.parsing import (
    common_options, endpoint_id_arg, endpoint_create_and_update_params)
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
    # require custom_concurrency and custom_parallelism for custom network_use
    if network_use == "custom" and (not custom_concurrency or
                                    not custom_parallelism):
        raise click.UsageError(
            "custom network_use level requires --custom-concurrency and "
            "--custom-parallelism to be set")

    # set max and preferred concurrency and parallelism based on args
    if custom_concurrency:
        max_concurrency, preferred_concurrency = custom_concurrency
    else:
        max_concurrency = None
        preferred_concurrency = None
    if custom_parallelism:
        max_parallelism, preferred_parallelism = custom_parallelism
    else:
        max_parallelism = None
        preferred_parallelism = None

    # location cannot be automatic and user defined
    if location_automatic and location:
        raise click.UsageError(
            "cannot combine --location and --location-automatic")

    # set location based on args
    if location_automatic:
        location = "Automatic"
    elif location:
        location = "{},{}".format(location[0], location[1])
    else:
        location = None

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
        disable_verify=disable_verify, location=location)

    client = get_client()
    res = client.update_endpoint(endpoint_id, ep_doc)

    if outformat_is_json():
        print_json_response(res)
    else:
        safeprint(res['message'])
