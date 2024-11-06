from __future__ import annotations

import datetime
import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.scopes import GCSCollectionScopeBuilder, Scope

from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager, is_client_login
from globus_cli.login_manager.utils import get_current_identity_id
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TimedeltaType,
    command,
    encrypt_data_option,
    fail_on_quota_errors_option,
    mutex_option_group,
    preserve_timestamp_option,
    skip_source_errors_option,
    sync_level_option,
    task_notify_option,
    transfer_batch_option,
    transfer_recursive_option,
    verify_checksum_option,
)
from globus_cli.termio import Field, display, formatters

from .._common import DATETIME_FORMATS, ScheduleFormatter

if t.TYPE_CHECKING:
    from globus_cli.services.auth import CustomAuthClient


FORMAT_FIELDS = [
    Field("Timer ID", "job_id"),
    Field("Name", "name"),
    Field("Type", "timer_type"),
    Field("Submitted At", "submitted_at", formatter=formatters.Date),
    Field("Status", "status"),
    Field("Last Run", "last_ran_at", formatter=formatters.Date),
    Field("Next Run", "next_run", formatter=formatters.Date),
    Field("Schedule", "schedule", formatter=ScheduleFormatter()),
    Field("Number of Runs", "number_of_runs"),
    Field("Number of Timer Errors", "number_of_errors"),
]


INTERVAL_HELP = """\
Interval at which the timer should run. Expressed in weeks, days, hours, minutes, and
seconds. Use 'w', 'd', 'h', 'm', and 's' as suffixes to specify.
e.g. '1h30m', '500s', '10d'
"""


@command("transfer", short_help="Create a recurring transfer timer.")
@click.argument(
    "source", metavar="SOURCE_ENDPOINT_ID[:SOURCE_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@click.argument(
    "destination", metavar="DEST_ENDPOINT_ID[:DEST_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@transfer_batch_option
@sync_level_option()
@transfer_recursive_option
@encrypt_data_option()
@verify_checksum_option
@preserve_timestamp_option()
@skip_source_errors_option
@fail_on_quota_errors_option
@task_notify_option
@click.option(
    "--start",
    type=click.DateTime(formats=DATETIME_FORMATS),
    help="Start time for the timer. Defaults to current time.",
)
@click.option(
    "--interval",
    type=TimedeltaType(),
    help=INTERVAL_HELP,
)
@click.option("--name", type=str, help="A name for the timer.")
@click.option(
    "--label",
    type=str,
    help="A label for the Transfer tasks submitted by the timer.",
)
@click.option(
    "--stop-after-date",
    type=click.DateTime(formats=DATETIME_FORMATS),
    help="Stop running the transfer after this date.",
)
@click.option(
    "--stop-after-runs",
    type=click.IntRange(min=1),
    help="Stop running the transfer after this number of runs have happened.",
)
@mutex_option_group("--stop-after-date", "--stop-after-runs")
@click.option(
    "--delete",
    is_flag=True,
    default=False,
    hidden=True,
    help=(
        "Delete any files in the destination directory not contained in the source. "
        'This results in "directory mirroring." Only valid on recursive transfers.'
    ),
)
@click.option(
    "--delete-destination-extra",
    is_flag=True,
    default=False,
    help=(
        "Delete any files in the destination directory not contained in the source. "
        'This results in "directory mirroring." Only valid on recursive transfers.'
    ),
)
@mutex_option_group("--delete", "--delete-destination-extra")
@LoginManager.requires_login("auth", "timer", "transfer")
def transfer_command(
    login_manager: LoginManager,
    *,
    name: str | None,
    source: tuple[uuid.UUID, str | None],
    destination: tuple[uuid.UUID, str | None],
    batch: t.TextIO | None,
    recursive: bool | None,
    start: datetime.datetime | None,
    interval: int | None,
    label: str | None,
    stop_after_date: datetime.datetime | None,
    stop_after_runs: int | None,
    delete: bool,
    delete_destination_extra: bool,
    sync_level: t.Literal["exists", "size", "mtime", "checksum"] | None,
    encrypt_data: bool,
    verify_checksum: bool,
    preserve_timestamp: bool,
    skip_source_errors: bool,
    fail_on_quota_errors: bool,
    notify: dict[str, bool],
) -> None:
    """
    Create a timer which will run a transfer on a recurring schedule
    according to the parameters provided.

    For example, to create a timer which runs a Transfer from /foo/ on one endpoint to
    /bar/ on another endpoint every day, with no end condition:

    \b
        globus timer create transfer --interval 1d --recursive $ep1:/foo/ $ep2:/bar/

    \b
    === Batch Input

    If you use `SOURCE_PATH` and `DEST_PATH` without the `--batch` flag, you
    will submit a single-file or single-directory timer.

    Using `--batch`, `globus timer create transfer` can create a timer which
    transfers multiple specified files or directories.
    Each line of `--batch` input is treated as a separate file or directory
    transfer to include in the timer.

    \b
    Lines are of the form
    [--recursive] [--external-checksum TEXT] SOURCE_PATH DEST_PATH\n

    Each line of the batch input is parsed like it would be at the command line.
    This means that if `SOURCE_PATH` or `DEST_PATH` contain spaces,
    the path should be wrapped in quotes, or the spaces should be escaped
    using a backslash character ("\\").

    Similarly, empty lines are skipped, and comments beginning with "#" are allowed.

    \b
    If you use `--batch` and supply a SOURCE_PATH and/or DEST_PATH via the commandline,
    these paths will be used as dir prefixes to any paths read from the `--batch` input.
    """
    from globus_cli.services.transfer import add_batch_to_transfer_data

    auth_client = login_manager.get_auth_client()
    transfer_client = login_manager.get_transfer_client()

    source_endpoint, cmd_source_path = source
    dest_endpoint, cmd_dest_path = destination

    if delete:
        msg = (
            "`--delete` has been deprecated and will be removed in a future release. "
            "Use `--delete-destination-extra` instead."
        )
        click.echo(click.style(msg, fg="yellow"), err=True)

    # avoid 'mutex_option_group', emit a custom error message
    if recursive is not None and batch:
        option_name = "--recursive" if recursive else "--no-recursive"
        raise click.UsageError(
            f"You cannot use `{option_name}` in addition to `--batch`. "
            f"Instead, use `{option_name}` on lines of `--batch` input which need it."
        )
    if recursive is False and (delete_destination_extra or delete):
        option_name = (
            "--delete-destination-extra" if delete_destination_extra else "--delete"
        )
        raise click.UsageError(
            f"The `{option_name}` option cannot be specified with `--no-recursive`."
        )
    if (cmd_source_path is None or cmd_dest_path is None) and (not batch):
        raise click.UsageError(
            "Transfer requires either `SOURCE_PATH` and `DEST_PATH` or `--batch`"
        )

    # Interval must be null iff the timer is 'once', i.e. stop-after-runs == 1.
    # and it must be non-null if the timer is 'recurring'
    schedule: globus_sdk.RecurringTimerSchedule | globus_sdk.OnceTimerSchedule
    start_ = resolve_optional_local_time(start)
    if stop_after_runs == 1:
        if interval is not None:
            raise click.UsageError("`--interval` is invalid with `--stop-after-runs=1`")
        schedule = globus_sdk.OnceTimerSchedule(datetime=start_)
    else:
        if interval is None:
            raise click.UsageError(
                "`--interval` is required unless `--stop-after-runs=1`"
            )

        end: dict[str, t.Any] | globus_sdk.MissingType = globus_sdk.MISSING
        # reminder: these two cases are mutex
        if stop_after_runs is not None:
            end = {
                "condition": "iterations",
                "count": stop_after_runs,
            }
        elif stop_after_date is not None:
            end = {
                "condition": "time",
                "datetime": resolve_optional_local_time(stop_after_date),
            }

        schedule = globus_sdk.RecurringTimerSchedule(
            interval_seconds=interval, end=end, start=start_
        )

    # default name, dynamically computed from the current time
    if name is None:
        now = datetime.datetime.now().isoformat()
        name = f"CLI Created Timer [{now}]"

    # check if either source or dest requires the data_access scope, and if so
    # prompt the user to go through the requisite login flow
    source_epish = Endpointish(source_endpoint, transfer_client=transfer_client)
    dest_epish = Endpointish(dest_endpoint, transfer_client=transfer_client)
    needs_data_access: list[str] = []
    if source_epish.requires_data_access_scope:
        needs_data_access.append(str(source_endpoint))
    if dest_epish.requires_data_access_scope:
        needs_data_access.append(str(dest_endpoint))

    # this list will only be populated *if* one of the two endpoints requires
    # data_access, so if it's empty, we can skip any handling
    if needs_data_access:
        scopes_needed = _derive_needed_scopes(needs_data_access)
        # If it's not a client login, we need to check
        # that the user has the required scopes
        if not is_client_login():
            request_data_access = _derive_missing_scopes(auth_client, scopes_needed)

            if request_data_access:
                scope_request_opts = " ".join(
                    f"--timer-data-access '{target}'" for target in request_data_access
                )
                click.echo(
                    f"""\
    A collection you are trying to use in this timer requires you to grant consent
    for the Globus CLI to access it.
    Please run

    globus session consent {scope_request_opts}

    to login with the required scopes."""
                )
                click.get_current_context().exit(4)

        # Otherwise, add requirements to the LoginManager
        login_manager.add_requirement(
            globus_sdk.TimerClient.scopes.resource_server,
            scopes=list(scopes_needed.values()),
        )

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
        delete_destination_extra=(delete or delete_destination_extra),
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

    timer_client = login_manager.get_timer_client()
    body = globus_sdk.TransferTimer(name=name, schedule=schedule, body=transfer_data)
    response = timer_client.create_timer(body)
    display(response["timer"], text_mode=display.RECORD, fields=FORMAT_FIELDS)


def resolve_optional_local_time(
    start: datetime.datetime | None,
) -> datetime.datetime | globus_sdk.utils.MissingType:
    if start is None:
        return globus_sdk.MISSING
    # set the timezone to local system time if the timezone input is not aware
    start_with_tz = start.astimezone() if start.tzinfo is None else start
    return start_with_tz


def _derive_needed_scopes(
    needs_data_access: list[str],
) -> dict[str, Scope]:
    # Render the fully nested scope strings for each target
    scopes_needed = {}
    for target in needs_data_access:
        target_scope = GCSCollectionScopeBuilder(target).data_access
        scopes_needed[target] = _ez_make_nested_scope(
            globus_sdk.TimerClient.scopes.timer,
            globus_sdk.TransferClient.scopes.all,
            target_scope,
        )
    return scopes_needed


def _derive_missing_scopes(
    auth_client: CustomAuthClient,
    scopes_needed: dict[str, Scope],
) -> list[str]:
    # read the identity ID stored from the login flow
    user_identity_id = get_current_identity_id()

    # get the user's Globus CLI consents
    consents = auth_client.get_consents(user_identity_id).to_forest()

    # check the 'needs_data_access' scope names against the 3rd-order dependencies
    # of the Timer scope and record the names of the ones which we need to request
    will_request_data_access: list[str] = []
    for name, scope_object in scopes_needed.items():
        if not consents.meets_scope_requirements([str(scope_object)]):
            will_request_data_access.append(name)

    # return these ultimately filtered requirements
    return will_request_data_access


# shorthand helper for constructing a nested scope
def _ez_make_nested_scope(*scope_strings: str) -> Scope:
    current_node = Scope(scope_strings[-1])
    for current_scope in scope_strings[-2::-1]:
        current_node = Scope(current_scope, dependencies=[current_node])
    return current_node
