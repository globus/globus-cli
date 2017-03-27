import click

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, ENDPOINT_PLUS_REQPATH,
    security_principal_opts)
from globus_cli.safeio import OutputFormatter

from globus_cli.services.auth import maybe_lookup_identity_id

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('create', help=('Create an access control rule, allowing new '
                               'permissions'))
@common_options
@security_principal_opts(allow_anonymous=True, allow_all_authenticated=True)
@click.option('--permissions', required=True,
              type=CaseInsensitiveChoice(('r', 'rw')),
              help='Permissions to add. Read-Only or Read/Write')
@click.argument('endpoint_plus_path', metavar=ENDPOINT_PLUS_REQPATH.metavar,
                type=ENDPOINT_PLUS_REQPATH)
def create_command(principal, permissions, endpoint_plus_path):
    """
    Executor for `globus endpoint permission create`
    """
    if not principal:
        raise click.UsageError(
            'A security principal is required for this command')

    endpoint_id, path = endpoint_plus_path
    principal_type, principal_val = principal

    client = get_client()

    if principal_type == 'identity':
        principal_val = maybe_lookup_identity_id(principal_val)

    rule_data = assemble_generic_doc(
        'access', permissions=permissions, principal=principal_val,
        principal_type=principal_type, path=path)

    res = client.add_endpoint_acl_rule(endpoint_id, rule_data)
    OutputFormatter(text_format=OutputFormatter.FORMAT_TEXT_RECORD,
                    fields=[('Message', 'message'), ('Rule ID', 'access_id')]
                    ).print_response(res)
