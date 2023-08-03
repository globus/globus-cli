from __future__ import annotations

import datetime
import sys
import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.scopes import GCSCollectionScopeBuilder, MutableScope

from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import (
    LoginManager,
    is_client_login,
    read_well_known_config,
)
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TimedeltaType,
    command,
    encrypt_data_option,
    fail_on_quota_errors_option,
    preserve_timestamp_option,
    skip_source_errors_option,
    sync_level_option,
    task_notify_option,
    transfer_batch_option,
    transfer_recursive_option,
    verify_checksum_option,
)
from globus_cli.termio import TextMode, display

from .._common import DATETIME_FORMATS, JOB_FORMAT_FIELDS

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

if t.TYPE_CHECKING:
    from globus_cli.services.auth import CustomAuthClient


INTERVAL_HELP = """\
Interval at which the job should run. Expressed in weeks, days, hours, minutes, and
seconds. Use 'w', 'd', 'h', 'm', and 's' as suffixes to specify.
e.g. '1h30m', '500s', '10d'
"""


def resolve_start_time(start: datetime.datetime | None) -> datetime.datetime:
    # handle the default start time (now)
    start_ = start or datetime.datetime.now()
    # set the timezone to local system time if the timezone input is not aware
    start_with_tz = start_.astimezone() if start_.tzinfo is None else start_
    return start_with_tz


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
@encrypt_data_option
@verify_checksum_option
@preserve_timestamp_option
@skip_source_errors_option
@fail_on_quota_errors_option
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
@LoginManager.requires_login("auth", "timer", "transfer")
def transfer_command(
    login_manager: LoginManager,
    *,
    name: str | None,
    source: tuple[uuid.UUID, str | None],
    destination: tuple[uuid.UUID, str | None],
    batch: t.TextIO | None,
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
) -> None:
    """
    Create a Timer job which will run a transfer on a recurring schedule
    according to the parameters provided.

    For example, to create a job which runs a Transfer from /foo/ on one endpoint to
    /bar/ on another endpoint every day, with no end condition:

    \b
        globus timer create transfer --interval 1d --recursive $ep1:/foo/ $ep2:/bar/
    """
    from globus_cli.services.transfer import add_batch_to_transfer_data, autoactivate

    auth_client = login_manager.get_auth_client()
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
            raise click.UsageError(
                "'--interval' is required unless `--stop-after-runs=1` is used."
            )

    # default name, dynamically computed from the current time
    if name is None:
        now = datetime.datetime.now().isoformat()
        name = f"CLI Created Timer [{now}]"

    # Check endpoint activation, figure out scopes needed.

    # the autoactivate helper may present output and exit in the case of v4 endpoints
    # which need activation (e.g. OA4MP)
    autoactivate(transfer_client, source_endpoint, if_expires_in=86400)
    autoactivate(transfer_client, dest_endpoint, if_expires_in=86400)

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
        # if the user is using client credentials, we cannot support the incremental
        # auth step in the current implementation
        #
        # TODO: think through how we can use the client creds to request the
        # requisite token in this case; it should be possible
        if is_client_login():
            raise click.UsageError(
                "Unsupported operation. When using client credentials, "
                "'globus timer create transfer' does not currently support "
                "collections which use the data_access scope: "
                f"{','.join(needs_data_access)}"
            )

        request_data_access = _derive_needed_scopes(auth_client, needs_data_access)

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

to login with the required scopes"""
            )
            click.get_current_context().exit(4)

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

    response = timer_client.create_job(
        globus_sdk.TimerJob.from_transfer_data(
            transfer_data,
            resolve_start_time(start),
            interval,
            name=name,
            stop_after=stop_after_date,
            stop_after_n=stop_after_runs,
            # the transfer AP scope string (without any dependencies)
            scope="https://auth.globus.org/scopes/actions.globus.org/transfer/transfer",
        )
    )
    display(response, text_mode=TextMode.text_record, fields=JOB_FORMAT_FIELDS)


def _derive_needed_scopes(
    auth_client: CustomAuthClient,
    needs_data_access: list[str],
) -> list[str]:
    # read the identity ID stored from the login flow
    # we will semi-gracefully handle the case of the data having been damaged/corrupted
    user_data = read_well_known_config("auth_user_data")
    if user_data is None:
        raise RuntimeError(
            "Identity ID was unexpectedly not visible in storage. "
            "A new login should fix the issue. "
            "Consider using `globus login --force`"
        )
    user_identity_id = user_data["sub"]

    # get the user's Globus CLI consents
    consents = auth_client.get_consents(user_identity_id)

    # check the 'needs_data_access' scope names against the 3rd-order dependencies
    # of the Timer scope and record the names of the ones which we need to request
    scopes_needed = {}
    for target in needs_data_access:
        target_scope = GCSCollectionScopeBuilder(target).data_access
        scopes_needed[target] = _ez_make_nested_scope(
            globus_sdk.TimerClient.scopes.timer,
            "https://auth.globus.org/scopes/actions.globus.org/transfer/transfer",
            globus_sdk.TransferClient.scopes.all,
            target_scope,
        )

    will_request_data_access: list[str] = []
    for name, scope_object in scopes_needed.items():
        if not consents.contains_scopes([scope_object]):
            will_request_data_access.append(name)

    # return these ultimately filtered requirements
    return will_request_data_access


# shorthand helper for constructing a nested scope
def _ez_make_nested_scope(*scope_strings: str) -> MutableScope:
    current_node = MutableScope(scope_strings[-1])
    for current_scope in scope_strings[-2::-1]:
        current_node = MutableScope(current_scope, dependencies=[current_node])
    return current_node
