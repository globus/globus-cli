import click
import inspect

from globus_cli.parsing import (
    common_options, endpoint_create_and_update_params, ENDPOINT_PLUS_REQPATH)
from globus_cli.helpers import (
    outformat_is_json, print_json_response, colon_formatted_print)
from globus_cli.services.transfer import (
    autoactivate, get_client, assemble_generic_doc)


COMMON_FIELDS = [
    ('Message', 'message'),
    ('Endpoint ID', 'id'),
]

GCP_FIELDS = [
    ('Setup Key', 'globus_connect_setup_key'),
]


def _validate_endpoint_create_params(params):
    """
    Given option params from endpoint create validates the options are valid
    """
    # options not allowed for shared endpoints
    if params["shared"]:
        # catch params with two option flags and thus two names
        if params["public"] is False:
            raise click.UsageError(
                "Option --private not allowed for shared endpoints")

        if params["force_encryption"] is False:
            raise click.UsageError("Option --no-force-encryption"
                                   " not allowed for shared endpoints")

        for option in ["myproxy_dn", "myproxy_server", "oauth_server",
                       "force_encryption", "default_directory", "public"]:
            if params[option] is not None:
                raise click.UsageError(
                    "Option --{} not allowed for "
                    "shared endpoints".format(option.replace("_", "-")))

    # options only allowed for GCS endpoints
    if params["endpoint_type"] != "server":
        # catch params with two option flags and thus two names
        if params["force_encryption"] is False:
            raise click.UsageError("Option --no-force-encryption only allowed "
                                   "for Globus Connect Server endpoints")

        for option in ["myproxy_dn", "myproxy_server", "oauth_server",
                       "force_encryption", "default_directory"]:
            if params[option] is not None:
                raise click.UsageError(
                    ("Option --{} only allowed for Globus Connect Server "
                     "endpoints".format(option.replace("_", "-"))))


@click.command('create', help='Create a new Endpoint')
@common_options
@endpoint_create_and_update_params(create=True)
@click.option('--globus-connect-server', 'endpoint_type', flag_value='server',
              help='This endpoint is a Globus Connect Server endpoint')
@click.option('--globus-connect-personal', 'endpoint_type',
              flag_value='personal', default=True, show_default=True,
              help='This endpoint is a Globus Connect Personal endpoint')
@click.option("--shared", default=None, type=ENDPOINT_PLUS_REQPATH,
              metavar=ENDPOINT_PLUS_REQPATH.metavar,
              help=("This endpoint is a shared endpoint hosted "
                    "on the given endpoint and path"))
def endpoint_create(endpoint_type, display_name, description, organization,
                    department, keywords, contact_email, contact_info,
                    info_link, public, default_directory, force_encryption,
                    oauth_server, myproxy_server, myproxy_dn, shared):
    """
    Executor for `globus endpoint create`
    """
    # validate params
    args, _, _, values = inspect.getargvalues(inspect.currentframe())
    params = dict((k, values[k]) for k in args)
    _validate_endpoint_create_params(params)

    # initialize values needed for all endpoint types
    client = get_client()
    is_globus_connect = endpoint_type == 'personal' or None

    # shared endpoint creation
    if shared:
        endpoint_id, host_path = shared

        ep_doc = assemble_generic_doc(
            'shared_endpoint',
            host_endpoint=endpoint_id, host_path=host_path,
            display_name=display_name, description=description,
            department=department, keywords=keywords,
            organization=organization, contact_email=contact_email,
            contact_info=contact_info, info_link=info_link, public=True)

        autoactivate(client, endpoint_id, if_expires_in=60)
        res = client.create_shared_endpoint(ep_doc)

    # non shared endpoint creation
    else:
        # omit `is_globus_connect` key if not GCP, otherwise include as `True`
        ep_doc = assemble_generic_doc(
            'endpoint',
            is_globus_connect=is_globus_connect,
            display_name=display_name, description=description,
            organization=organization, department=department,
            keywords=keywords, contact_email=contact_email,
            contact_info=contact_info, info_link=info_link,
            force_encryption=force_encryption, public=public,
            default_directory=default_directory,
            myproxy_server=myproxy_server, myproxy_dn=myproxy_dn,
            oauth_server=oauth_server)

        res = client.create_endpoint(ep_doc)

    # output response
    if outformat_is_json():
        print_json_response(res)
    else:
        fields = (COMMON_FIELDS + GCP_FIELDS if is_globus_connect
                  else COMMON_FIELDS)
        colon_formatted_print(res, fields)
