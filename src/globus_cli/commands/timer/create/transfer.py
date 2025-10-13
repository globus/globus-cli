from __future__ import annotations

import datetime
import typing as t
import uuid

import click
import globus_sdk
from globus_sdk.scopes import GCSCollectionScopes, Scope

from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager, is_client_login
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    command,
    encrypt_data_option,
    fail_on_quota_errors_option,
    filter_rule_options,
    mutex_option_group,
    preserve_timestamp_option,
    skip_source_errors_option,
    sync_level_option,
    task_notify_option,
    transfer_batch_option,
    transfer_recursive_option,
    verify_checksum_option,
)
from globus_cli.termio import display

from ._common import CREATE_FORMAT_FIELDS, TimerSchedule, timer_schedule_options

if t.TYPE_CHECKING:
    from globus_cli.services.auth import CustomAuthClient


INTERVAL_HELP = """\
Interval at which the timer should run. Expressed in weeks, days, hours, minutes, and
seconds. Use 'w', 'd', 'h', 'm', and 's' as suffixes to specify.
e.g. '1h30m', '500s', '10d'
"""


@command(
    "transfer",
    opts_to_combine={  # see 'filter_rule_options' for why this is needed
        "include": "filter_rules",
        "exclude": "filter_rules",
    },
    short_help="Create a recurring transfer timer.",
)
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
@filter_rule_options
@click.option("--name", type=str, help="A name for the timer.")
@timer_schedule_options
@click.option(
    "--label",
    type=str,
    help="A label for the Transfer tasks submitted by the timer.",
)
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
@LoginManager.requires_login("auth", "timers", "transfer")
def transfer_command(
    login_manager: LoginManager,
    *,
    name: str | None,
    schedule: TimerSchedule,
    source: tuple[uuid.UUID, str | None],
    destination: tuple[uuid.UUID, str | None],
    batch: t.TextIO | None,
    recursive: bool | globus_sdk.MissingType,
    label: str | globus_sdk.MissingType,
    delete: bool,
    delete_destination_extra: bool,
    sync_level: (
        t.Literal["exists", "size", "mtime", "checksum"] | globus_sdk.MissingType
    ),
    encrypt_data: bool,
    verify_checksum: bool,
    preserve_timestamp: bool,
    skip_source_errors: bool,
    fail_on_quota_errors: bool,
    filter_rules: list[tuple[t.Literal["include", "exclude"], str]],
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
    if recursive is not globus_sdk.MISSING and batch:
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
            request_data_access = _derive_missing_scopes(
                login_manager, auth_client, scopes_needed
            )

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
            globus_sdk.TimersClient.scopes.resource_server,
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

    for rule in filter_rules:
        method, name = rule
        transfer_data.add_filter_rule(method=method, name=name, type="file")

    if batch:
        add_batch_to_transfer_data(
            cmd_source_path, cmd_dest_path, globus_sdk.MISSING, transfer_data, batch
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
    display(response["timer"], text_mode=display.RECORD, fields=CREATE_FORMAT_FIELDS)


def _derive_needed_scopes(
    needs_data_access: list[str],
) -> dict[str, Scope]:
    # Render the fully nested scope strings for each target
    scopes_needed = {}
    for target in needs_data_access:
        # FIXME: the target scope should be made optional (atomically revocable)
        target_scope = GCSCollectionScopes(target).data_access
        timers_scope = globus_sdk.TimersClient.scopes.timer
        transfer_scope = globus_sdk.TransferClient.scopes.all

        scopes_needed[target] = timers_scope.with_dependency(
            transfer_scope.with_dependency(target_scope)
        )
    return scopes_needed


def _derive_missing_scopes(
    login_manager: LoginManager,
    auth_client: CustomAuthClient,
    scopes_needed: dict[str, Scope],
) -> list[str]:
    # read the identity ID stored from the login flow
    user_identity_id = login_manager.get_current_identity_id()

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
