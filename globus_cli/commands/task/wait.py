import click
import sys

from globus_cli.safeio import safeprint
from globus_cli.parsing import HiddenOption, common_options, task_id_arg
from globus_cli.safeio import formatted_print, FORMAT_SILENT

from globus_cli.services.transfer import get_client


@click.command('wait', help='Wait for a Task to complete')
@common_options
@task_id_arg
@click.option('--timeout', type=int, metavar='N',
              help=('Wait N seconds. If the Task does not terminate by '
                    'then, or terminates with an unsuccessful status, '
                    'exit with status 1'))
@click.option('--polling-interval', default=1, type=int, show_default=True,
              help='Number of seconds between Task status checks.')
@click.option('--heartbeat', '-H', is_flag=True,
              help=('Every polling interval, print "." to stdout to '
                    'indicate that task wait is till active'))
@click.option('--meow', is_flag=True, cls=HiddenOption)
def task_wait(meow, heartbeat, polling_interval, timeout, task_id):
    """
    Executor for `globus task wait`
    """
    if polling_interval < 1:
        raise click.UsageError(
            '--polling-interval={0} was less than minimum of {1}'
            .format(polling_interval, 1))

    client = get_client()

    def timed_out(waited_time):
        if timeout is None:
            return False
        else:
            return waited_time >= timeout

    def check_completed():
        completed = client.task_wait(task_id, timeout=polling_interval,
                                     polling_interval=polling_interval)
        if completed:
            if heartbeat:
                safeprint('', write_to_stderr=True)
            # meowing tasks wake up!
            if meow:
                safeprint("""\
                  _..
  /}_{\           /.-'
 ( a a )-.___...-'/
 ==._.==         ;
      \ i _..._ /,
      {_;/   {_//""", write_to_stderr=True)

            # TODO: possibly update TransferClient.task_wait so that we don't
            # need to do an extra fetch to get the task status after completion
            res = client.get_task(task_id)
            formatted_print(res, text_format=FORMAT_SILENT)

            status = res['status']
            if status == 'SUCCEEDED':
                click.get_current_context().exit(0)
            else:
                click.get_current_context().exit(1)

        return completed

    # Tasks start out sleepy
    if meow:
        safeprint("""\
   |\      _,,,---,,_
   /,`.-'`'    -.  ;-;;,_
  |,4-  ) )-,_..;\ (  `'-'
 '---''(_/--'  `-'\_)""", write_to_stderr=True)

    waited_time = 0
    while (not timed_out(waited_time) and
           not check_completed()):
        if heartbeat:
            safeprint('.', write_to_stderr=True, newline=False)
            sys.stderr.flush()

        waited_time += polling_interval

    # add a trailing newline to heartbeats if we fail
    if heartbeat:
        safeprint('', write_to_stderr=True)

    # output json if requested, but nothing for text mode
    res = client.get_task(task_id)
    formatted_print(res, text_format=FORMAT_SILENT)

    click.get_current_context().exit(1)
