import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.safeio import formatted_print

from globus_cli.services.auth import lookup_identity_name

from globus_cli.services.transfer import get_client


def principal_str(role):
    principal = role['principal']
    if role['principal_type'] == 'identity':
        principal = lookup_identity_name(principal)
    return principal


@click.command('list', help='List of assigned Roles on an Endpoint')
@common_options
@endpoint_id_arg
def role_list(endpoint_id):
    """
    Executor for `globus access endpoint-role-list`
    """
    client = get_client()
    roles = client.endpoint_role_list(endpoint_id)

    formatted_print(roles, fields=[
        ('Principal Type', 'principal_type'), ('Role ID', 'id'),
        ('Principal', principal_str), ('Role', 'role')])
