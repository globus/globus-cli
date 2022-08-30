from __future__ import annotations

import datetime
import sys
from typing import TextIO

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TimedeltaType,
    command,
    sync_level_option,
    task_notify_option,
    transfer_batch_option,
    transfer_recursive_option,
)
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print

from .._common import DATETIME_FORMATS, JOB_FORMAT_FIELDS

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

# XXX: this may need to be parametrized over data_access scopes?
_TRANSFER_AP_SCOPE = (
    "https://auth.globus.org/scopes/actions.globus.org/transfer/transfer"
)


INTERVAL_HELP = """\
Interval at which the job should run. Expressed in weeks, days, hours, minutes, and
seconds. Use 'w', 'd', 'h', 'm', and 's' as suffixes to specify.
e.g. '1h30m', '500s', '10d'
"""


@command("transfer", short_help="Create a recurring transfer job in Timer")
@click.argument(
    "source", metavar="SOURCE_ENDPOINT_ID[:SOURCE_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@click.argument(
    "destination", metavar="DEST_ENDPOINT_ID[:DEST_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@transfer_batch_option
@sync_level_option
@transfer_recursive_option
@task_notify_option
@click.option(
    "--start",
    type=click.DateTime(formats=DATETIME_FORMATS),
    help="Start time for the job. Defaults to current time",
)
@click.option(
    "--interval",
    type=TimedeltaType(),
    help=INTERVAL_HELP,
)
@click.option("--name", type=str, help="A name for the Timer job")
@click.option(
    "--label",
    type=str,
    help="A label for the Transfer tasks submitted by the Timer job",
)
@click.option(
    "--stop-after-date",
    type=click.DateTime(formats=DATETIME_FORMATS),
    help="Stop running the transfer after this date",
)
@click.option(
    "--stop-after-runs",
    type=click.IntRange(min=1),
    help="Stop running the transfer after this number of runs have happened",
)
@click.option(
    "--encrypt-data",
    is_flag=True,
    help="Encrypt data sent through the network using TLS",
)
@click.option(
    "--verify-checksum",
    is_flag=True,
    help="Verify file checksums and retry if the source and destination don't match",
)
@click.option(
    "--preserve-timestamp",
    is_flag=True,
    help="Set file timestamps on the destination to match the origin",
)
@click.option(
    "--skip-source-errors",
    is_flag=True,
    default=False,
    help="Skip files or directories on the source endpoint that hit PERMISSION_DENIED "
    "or FILE_NOT_FOUND errors",
)
@click.option(
    "--fail-on-quota-errors",
    is_flag=True,
    default=False,
    help="Cancel the submitted tasks if QUOTA_EXCEEDED errors are hit",
)
@LoginManager.requires_login(LoginManager.TIMER_RS, LoginManager.TRANSFER_RS)
def transfer_command(
    login_manager: LoginManager,
    name: str | None,
    source: tuple[str, str | None],
    destination: tuple[str, str | None],
    batch: TextIO | None,
    recursive: bool,
    start: datetime.datetime | None,
    interval: int | None,
    label: str | None,
    stop_after_date: datetime.datetime | None,
    stop_after_runs: int | None,
    sync_level: Literal["exists", "size", "mtime", "checksum"] | None,
    encrypt_data: bool,
    verify_checksum: bool,
    preserve_timestamp: bool,
    skip_source_errors: bool,
    fail_on_quota_errors: bool,
    notify: dict[str, bool],
):
    """
    Create a Timer job which will run a transfer on a recurring schedule
    according to the parameters provided.

    For example, to create a job which runs a Transfer from /foo/ on one endpoint to
    /bar/ on another endpoint every day, with no end condition:

    \b
        globus timer create transfer --interval 1d --recursive $ep1:/foo/ $ep2:/bar/
    """
    from globus_cli.services.transfer import add_batch_to_transfer_data, autoactivate

    timer_client = login_manager.get_timer_client()
    transfer_client = login_manager.get_transfer_client()

    source_endpoint, cmd_source_path = source
    dest_endpoint, cmd_dest_path = destination

    # avoid 'mutex_option_group', emit a custom error message
    if recursive and batch:
        raise click.UsageError(
            "You cannot use --recursive in addition to --batch. "
            "Instead, use --recursive on lines of --batch input "
            "which need it"
        )
    if (cmd_source_path is None or cmd_dest_path is None) and (not batch):
        raise click.UsageError(
            "transfer requires either SOURCE_PATH and DEST_PATH or --batch"
        )

    # Interval must be null iff the job is non-repeating, i.e. stop-after-runs == 1.
    if stop_after_runs != 1:
        if interval is None:
            raise click.UsageError("Missing option '--interval'")

    # default name, dynamically computed from the current time
    if name is None:
        now = datetime.datetime.now().isoformat()
        name = f"CLI Created Timer [{now}]"

    # Check endpoint activation, figure out scopes needed.

    # Note this will provide help text on activating endpoints.
    autoactivate(transfer_client, source_endpoint, if_expires_in=86400)
    autoactivate(transfer_client, dest_endpoint, if_expires_in=86400)

    # XXX: this section needs to be re-evaluated when 'timer create transfer' gets more
    # capabilities to handle endpoints with scope requirements
    # this would likely be the place to insert scope related checks

    transfer_data = globus_sdk.TransferData(
        source_endpoint=source_endpoint,
        destination_endpoint=dest_endpoint,
        label=label,
        sync_level=sync_level,
        verify_checksum=verify_checksum,
        preserve_timestamp=preserve_timestamp,
        encrypt_data=encrypt_data,
        skip_source_errors=skip_source_errors,
        fail_on_quota_errors=fail_on_quota_errors,
        # mypy can't understand kwargs expansion very well
        **notify,  # type: ignore[arg-type]
    )

    if batch:
        add_batch_to_transfer_data(
            cmd_source_path, cmd_dest_path, None, transfer_data, batch
        )
    elif cmd_source_path is not None and cmd_dest_path is not None:
        transfer_data.add_item(
            cmd_source_path,
            cmd_dest_path,
            recursive=recursive,
        )
    else:  # unreachable
        raise NotImplementedError()

    start_with_tz = start or datetime.datetime.now()
    if start_with_tz.tzinfo is None:
        start_with_tz = start_with_tz.astimezone()
    response = timer_client.create_job(
        globus_sdk.TimerJob.from_transfer_data(
            transfer_data,
            start_with_tz,
            interval,
            name=name,
            stop_after=stop_after_date,
            stop_after_n=stop_after_runs,
            scope=_TRANSFER_AP_SCOPE,
        )
    )
    formatted_print(response, text_format=FORMAT_TEXT_RECORD, fields=JOB_FORMAT_FIELDS)
