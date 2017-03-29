import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RAW

from globus_cli.services.transfer import get_client


@click.command('delete', help=('Delete an access control rule, removing '
                               'permissions'))
@common_options
@endpoint_id_arg
@click.argument('rule_id')
def delete_command(endpoint_id, rule_id):
    """
    Executor for `globus endpoint permission delete`
    """
    client = get_client()

    res = client.delete_endpoint_acl_rule(endpoint_id, rule_id)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key='message')
