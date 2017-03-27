import click

from globus_cli.parsing import common_options, endpoint_id_arg
from globus_cli.services.transfer import get_client
from globus_cli.safeio import OutputFormatter


@click.command('is-activated', short_help='Check if an Endpoint is activated',
               help=('Check if an Endpoint is activated or requires '
                     'activation. If it requires activation, exits with '
                     'status 1, otherwise exits with status 0.'))
@common_options
@endpoint_id_arg
@click.option('--until', type=int,
              help=('An integer number of seconds in the future. If the '
                    'endpoint is activated, but will expire by then, exits '
                    'with status 1'))
@click.option('--absolute-time', is_flag=True,
              show_default=True, default=False,
              help=('Treat the value of --until as a POSIX timestamp (seconds '
                    'since Epoch), not a number of seconds into the future.'))
def endpoint_is_activated(endpoint_id, until, absolute_time):
    """
    Executor for `globus endpoint is-activated`
    """
    client = get_client()
    res = client.endpoint_get_activation_requirements(endpoint_id)
    formatter = OutputFormatter()

    def fail(deadline=None):
        exp_string = ''
        if deadline is not None:
            exp_string = ' or will expire before {}'.format(deadline)

        formatter.print_response(
            res, simple_text=(
                '{0} is not activated{1}\n'
                'To activate, please go to the following page:\n\n'
                '  https://www.globus.org/app/endpoints/{0}/activate\n'
                ).format(endpoint_id, exp_string))
        click.get_current_context().exit(1)

    def success(msg, *format_params):
        formatter.print_response(
            res, simple_text=(msg.format(endpoint_id, *format_params)))
        click.get_current_context().exit(0)

    # eternally active endpoints have a special expires_in value
    if res['expires_in'] == -1:
        success('{} does not require activation')

    # if --until was not passed
    if until is None:
        # and we are active right now (0s in the future)...
        if res.active_until(0):
            success('{} is activated')
        # or we are not active
        fail()

    # autoactivation is not supported and --until was passed
    if res.active_until(until, relative_time=not absolute_time):
        success('{} will be active until {}', until)
    else:
        fail(deadline=until)
