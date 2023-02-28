from __future__ import annotations

import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, synchronous_task_wait_options

from .._common import transfer_task_wait_with_io
from ._common import task_id_arg


@command(
    "wait",
    short_help="Wait for a task to complete",
    adoc_output="""
When text output is requested, no output is written to standard out. All output
is written to standard error.

When JSON output is requested, the standard error output remains, but the task
status after waiting will be sent to stdout.
""",
    adoc_examples="""
Wait 30 seconds for a task to complete, printing heartbeats to stderr and
producing a JSON description of the task at the end:

[source,bash]
----
$ globus task wait --timeout 30 -H --format json TASK_ID
----

Wait for a task without limit, silently, polling every 5 minutes:

[source,bash]
----
$ globus task wait --polling-interval 300 TASK_ID
----
""",
)
@task_id_arg()
@synchronous_task_wait_options
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def task_wait(
    *,
    login_manager: LoginManager,
    meow: bool,
    heartbeat: bool,
    polling_interval: int,
    timeout: int | None,
    task_id: uuid.UUID,
    timeout_exit_code: int,
) -> None:
    """
    Wait for a task to complete.

    This command waits until the timeout is reached, checking every 'M' seconds
    (where 'M' is the polling interval).

    If the task succeeds by then, it exits with status 0. Otherwise, it exits with
    status 1.
    """
    transfer_client = login_manager.get_transfer_client()
    transfer_task_wait_with_io(
        transfer_client,
        meow,
        heartbeat,
        polling_interval,
        timeout,
        task_id,
        timeout_exit_code,
    )
