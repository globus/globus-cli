import click

from globus_cli.parsing import common_options, task_id_arg
from globus_cli.output_formatter import OutputFormatter

from globus_cli.services.transfer import get_client


EXPLICIT_PAUSE_MSG_FIELDS = [
    ('Source Endpoint', 'source_pause_message'),
    ('Source Shared Endpoint', 'source_pause_message_share'),
    ('Destination Endpoint', 'destination_pause_message'),
    ('Destination Shared Endpoint', 'destination_pause_message_share'),
]

PAUSE_RULE_OPERATION_FIELDS = [
    ('write', 'pause_task_transfer_write'),
    ('read', 'pause_task_transfer_read'),
    ('delete', 'pause_task_delete'),
    ('rename', 'pause_rename'),
    ('mkdir', 'pause_mkdir'),
    ('ls', 'pause_ls'),
]

PAUSE_RULE_DISPLAY_FIELDS = [
    ('Operations', lambda rule: '/'.join(label for label, key
                                         in PAUSE_RULE_OPERATION_FIELDS
                                         if rule[key])),
    ('On Endpoint', 'endpoint_display_name'),
    ('All Users', lambda rule: 'No' if rule['identity_id'] else 'Yes'),
    ('Message', 'message'),
]


@click.command('pause-info',
               help='Show messages from activity managers who have explicitly '
                    'paused the given in-progress task and list any active '
                    'pause rules that apply to it',
               short_help='Show why an in-progress task is currently paused')
@common_options
@task_id_arg
def task_pause_info(task_id):
    """
    Executor for `globus task pause-info`
    """
    client = get_client()
    res = client.task_pause_info(task_id)

    def _custom_text_format(res):
        explicit_pauses = [
            field for field in EXPLICIT_PAUSE_MSG_FIELDS
            # n.b. some keys are absent for completed tasks
            if res.get(field[1])
        ]
        effective_pause_rules = res['pause_rules']

        if not explicit_pauses and not effective_pause_rules:
            raise click.ClickException(
                'Task {} is not paused.'.format(task_id))

        if explicit_pauses:
            formatter = OutputFormatter(fields=explicit_pauses,
                                        text_format='text_record')
            formatter.print_response(
                res, text_preamble='This task has been explicitly paused.\n',
                text_epilog='\n' if effective_pause_rules else None)

        if effective_pause_rules:
            formatter = OutputFormatter(fields=PAUSE_RULE_DISPLAY_FIELDS)
            formatter.print_response(effective_pause_rules, text_preamble=(
                'The following pause rules are effective on this task:\n'))

    OutputFormatter(text_format=_custom_text_format).print_response(res)
