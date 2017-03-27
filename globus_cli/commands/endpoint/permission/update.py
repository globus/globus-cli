import click

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, endpoint_id_arg)
from globus_cli.safeio import OutputFormatter

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('update', help=('Update an access control rule, changing '
                               'permissions on an endpoint'))
@endpoint_id_arg
@common_options
@click.argument('rule_id')
@click.option('--permissions', required=True,
              type=CaseInsensitiveChoice(('r', 'rw')),
              help='Permissions to add. Read-Only or Read/Write')
def update_command(permissions, rule_id, endpoint_id):
    """
    Executor for `globus endpoint permission update`
    """
    client = get_client()

    rule_data = assemble_generic_doc('access', permissions=permissions)
    res = client.update_endpoint_acl_rule(endpoint_id, rule_id, rule_data)
    OutputFormatter(text_format=OutputFormatter.FORMAT_TEXT_RAW,
                    response_key='message').print_response(res)
