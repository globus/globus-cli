from __future__ import annotations

import uuid

import click
import globus_sdk
from globus_sdk.paging import Paginator

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, mutex_option_group
from globus_cli.termio import Field, TextMode, display

from ._common import task_id_arg

COMMON_FIELDS = [
    Field("Label", "label"),
    Field("Task ID", "task_id"),
    Field("Is Paused", "is_paused"),
    Field("Type", "type"),
    Field("Directories", "directories"),
    Field("Files", "files"),
    Field("Status", "status"),
    Field("Request Time", "request_time"),
    Field("Faults", "faults"),
    Field("Total Subtasks", "subtasks_total"),
    Field("Subtasks Succeeded", "subtasks_succeeded"),
    Field("Subtasks Pending", "subtasks_pending"),
    Field("Subtasks Retrying", "subtasks_retrying"),
    Field("Subtasks Failed", "subtasks_failed"),
    Field("Subtasks Canceled", "subtasks_canceled"),
    Field("Subtasks Expired", "subtasks_expired"),
    Field("Subtasks with Skipped Errors", "subtasks_skipped_errors"),
]

ACTIVE_FIELDS = [Field("Deadline", "deadline"), Field("Details", "nice_status")]

COMPLETED_FIELDS = [Field("Completion Time", "completion_time")]

DELETE_FIELDS = [
    Field("Endpoint", "source_endpoint_display_name"),
    Field("Endpoint ID", "source_endpoint_id"),
]

TRANSFER_FIELDS = [
    Field("Source Endpoint", "source_endpoint_display_name"),
    Field("Source Endpoint ID", "source_endpoint_id"),
    Field("Destination Endpoint", "destination_endpoint_display_name"),
    Field("Destination Endpoint ID", "destination_endpoint_id"),
    Field("Bytes Transferred", "bytes_transferred"),
    Field("Bytes Per Second", "effective_bytes_per_second"),
]

SUCCESSFULL_TRANSFER_FIELDS = [
    Field("Source Path", "source_path"),
    Field("Destination Path", "destination_path"),
]

SKIPPED_PATHS_FIELDS = [
    Field("Source Path", "source_path"),
    Field("Destination Path", "destination_path"),
    Field("Error Code", "error_code"),
]


def print_successful_transfers(
    client: globus_sdk.TransferClient, task_id: uuid.UUID
) -> None:
    from globus_cli.services.transfer import iterable_response_to_dict

    paginator = Paginator.wrap(client.task_successful_transfers)
    res = paginator(task_id).items()
    display(
        res,
        fields=SUCCESSFULL_TRANSFER_FIELDS,
        json_converter=iterable_response_to_dict,
    )


def print_skipped_errors(client: globus_sdk.TransferClient, task_id: uuid.UUID) -> None:
    from globus_cli.services.transfer import iterable_response_to_dict

    paginator = Paginator.wrap(client.task_skipped_errors)
    res = paginator(task_id).items()
    display(
        res,
        fields=SKIPPED_PATHS_FIELDS,
        json_converter=iterable_response_to_dict,
    )


def print_task_detail(client: globus_sdk.TransferClient, task_id: uuid.UUID) -> None:
    res = client.get_task(task_id)
    display(
        res,
        text_mode=TextMode.text_record,
        fields=(
            COMMON_FIELDS
            + (COMPLETED_FIELDS if res["completion_time"] else ACTIVE_FIELDS)
            + (DELETE_FIELDS if res["type"] == "DELETE" else TRANSFER_FIELDS)
        ),
    )


@command(
    "show",
    short_help="Show detailed information about a task",
    adoc_output="""
When text output is requested, output varies slightly between 'TRANSFER' and
'DELETE' tasks, and between active and completed tasks.

All of the following which apply will be shown:

- 'Task ID'
- 'Type'
- 'Status'
- 'Is Paused'
- 'Label'
- 'Files'
- 'Directories'
- 'Source Endpoint'
- 'Source Endpoint ID'
- 'Destination Endpoint'
- 'Destination Endpoint ID'
- 'Endpoint'
- 'Endpoint ID'
- 'Completion Time'
- 'Deadline'
- 'Details'
- 'Request Time'
- 'Bytes Transferred'
- 'Bytes Per Second'
- 'Faults'
- 'Total Subtasks'
- 'Subtasks Succeeded'
- 'Subtasks Pending'
- 'Subtasks Retrying'
- 'Subtasks Failed'
- 'Subtasks Canceled'
- 'Subtasks Expired'

If *--successful-transfers* is given, the following fields are used:

- 'Source Path'
- 'Destination Path'
""",
    adoc_examples="""Show detailed info about a task as text

[source,bash]
----
$ globus task show TASK_ID
----
""",
)
@task_id_arg()
@click.option(
    "--successful-transfers",
    "-t",
    is_flag=True,
    default=False,
    help=(
        "Show files that were transferred as result of this task. "
        "Mutually exclusive with --skipped-errors"
    ),
)
@click.option(
    "--skipped-errors",
    is_flag=True,
    default=False,
    help=(
        "Show paths that were skipped due to errors during this task. "
        "Mutually exclusive with --successful-transfers"
    ),
)
@mutex_option_group("--successful-transfers", "--skipped-errors")
@LoginManager.requires_login("transfer")
def show_task(
    *,
    login_manager: LoginManager,
    successful_transfers: bool,
    skipped_errors: bool,
    task_id: uuid.UUID,
) -> None:
    """
    Print information detailing the status and other info about a task.

    The task may be pending, completed, or in progress.
    """
    transfer_client = login_manager.get_transfer_client()

    if successful_transfers:
        print_successful_transfers(transfer_client, task_id)
    elif skipped_errors:
        print_skipped_errors(transfer_client, task_id)
    else:
        print_task_detail(transfer_client, task_id)
