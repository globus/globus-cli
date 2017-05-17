import click

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, security_principal_opts,
    endpoint_plus_path_options, parse_endpoint_plus_path)
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RECORD

from globus_cli.services.auth import maybe_lookup_identity_id

from globus_cli.services.transfer import get_client, assemble_generic_doc


@click.command('create', help=('Create an access control rule, allowing new '
                               'permissions'))
@common_options
@security_principal_opts(allow_anonymous=True, allow_all_authenticated=True)
@click.option('--permissions', required=True,
              type=CaseInsensitiveChoice(('r', 'rw')),
              help='Permissions to add. Read-Only or Read/Write')
@endpoint_plus_path_options(path_required=True)
def create_command(principal, permissions, endpoint_plus_path, bookmark):
    """
    Executor for `globus endpoint permission create`
    """
    if not principal:
        raise click.UsageError(
            'A security principal is required for this command')

    endpoint_id, path = parse_endpoint_plus_path(
        endpoint_plus_path, bookmark, path_required=True)
    principal_type, principal_val = principal

    client = get_client()

    if principal_type == 'identity':
        principal_val = maybe_lookup_identity_id(principal_val)

    rule_data = assemble_generic_doc(
        'access', permissions=permissions, principal=principal_val,
        principal_type=principal_type, path=path)

    res = client.add_endpoint_acl_rule(endpoint_id, rule_data)
    formatted_print(res, text_format=FORMAT_TEXT_RECORD,
                    fields=[('Message', 'message'), ('Rule ID', 'access_id')])
