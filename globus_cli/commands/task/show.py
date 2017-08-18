import click

from globus_cli.parsing import common_options, task_id_arg
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RECORD

from globus_cli.services.transfer import get_client, iterable_response_to_dict


COMMON_FIELDS = [
    ('Label', 'label'),
    ('Task ID', 'task_id'),
    ('Is Paused', 'is_paused'),
    ('Type', 'type'),
    ('Directories', 'directories'),
    ('Files', 'files'),
    ('Status', 'status'),
    ('Request Time', 'request_time'),
    ('Faults', 'faults'),
    ('Total Subtasks', 'subtasks_total'),
    ('Subtasks Succeeded', 'subtasks_succeeded'),
    ('Subtasks Pending', 'subtasks_pending'),
    ('Subtasks Retrying', 'subtasks_retrying'),
    ('Subtasks Failed', 'subtasks_failed'),
    ('Subtasks Canceled', 'subtasks_canceled'),
    ('Subtasks Expired', 'subtasks_expired'),
]

ACTIVE_FIELDS = [
    ('Deadline', 'deadline'),
    ('Details', 'nice_status'),
]

COMPLETED_FIELDS = [
    ('Completion Time', 'completion_time'),
]

DELETE_FIELDS = [
    ('Endpoint', 'source_endpoint_display_name'),
    ('Endpoint ID', 'source_endpoint_id'),
]

TRANSFER_FIELDS = [
    ('Source Endpoint', 'source_endpoint_display_name'),
    ('Source Endpoint ID', 'source_endpoint_id'),
    ('Destination Endpoint', 'destination_endpoint_display_name'),
    ('Destination Endpoint ID', 'destination_endpoint_id'),
    ('Bytes Transferred', 'bytes_transferred'),
    ('Bytes Per Second', 'effective_bytes_per_second'),
    ('Symlinks', 'symlinks'), ('Recursive Symlinks', 'recursive_symlinks')
]

SUCCESSFULL_TRANSFER_FIELDS = [
    ('Source Path', 'source_path'),
    ('Destination Path', 'destination_path')
]


def print_successful_transfers(client, task_id):
    res = client.task_successful_transfers(task_id, num_results=None)
    formatted_print(res, fields=SUCCESSFULL_TRANSFER_FIELDS,
                    json_converter=iterable_response_to_dict)


def print_task_detail(client, task_id):
    res = client.get_task(task_id)
    formatted_print(res, text_format=FORMAT_TEXT_RECORD, fields=(
        COMMON_FIELDS +
        (COMPLETED_FIELDS if res['completion_time'] else ACTIVE_FIELDS) +
        (DELETE_FIELDS if res['type'] == 'DELETE' else TRANSFER_FIELDS)))


@click.command('show', help='Show detailed information about a specific task')
@common_options
@task_id_arg
@click.option('--successful-transfers', '-t', is_flag=True, default=False,
              help='Show files that were transferred as result of this task.')
def show_task(successful_transfers, task_id):
    """
    Executor for `globus task show`
    """
    client = get_client()

    if successful_transfers:
        print_successful_transfers(client, task_id)
    else:
        print_task_detail(client, task_id)
