import click

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, endpoint_id_arg,
    security_principal_opts)
from globus_cli.output_formatter import OutputFormatter

from globus_cli.services.auth import maybe_lookup_identity_id

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('create', help='Create a Role on an Endpoint')
@common_options
@endpoint_id_arg
@security_principal_opts
@click.option('--role', required=True,
              type=CaseInsensitiveChoice(
                  ('administrator', 'access_manager', 'activity_manager',
                   'activity_monitor')),
              help='A role to assign.')
def role_create(role, principal, endpoint_id):
    """
    Executor for `globus endpoint role show`
    """
    principal_type, principal_val = principal

    client = get_client()

    if principal_type == 'identity':
        principal_val = maybe_lookup_identity_id(principal_val)

    role_doc = assemble_generic_doc(
        'role', principal_type=principal_type, principal=principal_val,
        role=role)

    res = client.add_endpoint_role(endpoint_id, role_doc)
    OutputFormatter().print_response(
        res, simple_text='ID: {}'.format(res['id']))
