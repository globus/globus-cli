from __future__ import annotations

import datetime
import sys
import typing as t
import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    command,
    encrypt_data_option,
    fail_on_quota_errors_option,
    mutex_option_group,
    preserve_timestamp_option,
    skip_source_errors_option,
    sync_level_option,
    task_submission_options,
    transfer_batch_option,
    transfer_recursive_option,
    verify_checksum_option,
)
from globus_cli.termio import Field, TextMode, display

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


@command(
    "transfer",
    short_help="Submit a transfer task (asynchronous)",
    adoc_examples="""Transfer a single file:

[source,bash]
----
$ source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ dest_ep=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus transfer $source_ep:/share/godata/file1.txt $dest_ep:~/mynewfile.txt
----

Transfer a directory recursively:

[source,bash]
----
$ source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ dest_ep=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus transfer $source_ep:/share/godata/ $dest_ep:~/mynewdir/ --recursive
----

Use the batch input method to transfer multiple files and directories:

[source,bash]
----
$ source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ dest_ep=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus transfer $source_ep $dest_ep --batch -
# lines starting with '#' are comments
# and blank lines (for spacing) are allowed

# files in the batch
/share/godata/file1.txt ~/myfile1.txt
/share/godata/file2.txt ~/myfile2.txt
/share/godata/file3.txt ~/myfile3.txt
# these are recursive transfers in the batch
# you can use -r, --recursive, and put the option before or after
/share/godata ~/mygodatadir -r
--recursive godata mygodatadir2
<EOF>
----

Use the batch input method to transfer multiple files and directories, with a
prefix on the source and destination endpoints (this is identical to the case
above, but much more concise):

[source,bash]
----
$ source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ dest_ep=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus transfer $source_ep:/share/ $dest_ep:~/ --batch -
godata/file1.txt myfile1.txt
godata/file2.txt myfile2.txt
godata/file3.txt myfile3.txt
godata mygodatadir -r
--recursive godata mygodatadir2
<EOF>
----


Consume a batch of files to transfer from a data file, submit the transfer
task, get back its task ID for use in `globus task wait`, wait for up to 30
seconds for the task to complete, and then print a success or failure message.

[source,bash]
----
$ cat my_file_batch.txt
/share/godata/file1.txt ~/myfile1.txt
/share/godata/file2.txt ~/myfile2.txt
/share/godata/file3.txt ~/myfile3.txt
----

[source,bash]
----
source_ep=ddb59aef-6d04-11e5-ba46-22000b92c6ec
dest_ep=ddb59af0-6d04-11e5-ba46-22000b92c6ec

task_id="$(globus transfer $source_ep $dest_ep \
    --jmespath 'task_id' --format=UNIX \
    --batch my_file_batch.txt)"

echo "Waiting on 'globus transfer' task '$task_id'"
globus task wait "$task_id" --timeout 30
if [ $? -eq 0 ]; then
    echo "$task_id completed successfully";
else
    echo "$task_id failed!";
fi
----
""",
)
@click.argument(
    "source", metavar="SOURCE_ENDPOINT_ID[:SOURCE_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@click.argument(
    "destination", metavar="DEST_ENDPOINT_ID[:DEST_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@task_submission_options
@sync_level_option(aliases=("-s",))
@transfer_batch_option
@transfer_recursive_option
@preserve_timestamp_option(aliases=("--preserve-mtime",))
@verify_checksum_option
@encrypt_data_option(aliases=("--encrypt",))
@skip_source_errors_option
@fail_on_quota_errors_option
@click.option(
    "--delete",
    is_flag=True,
    default=False,
    help=(
        "Delete extraneous files in the destination directory. "
        "Only applies to recursive directory transfers."
    ),
)
@click.option(
    "--external-checksum",
    help=(
        "An external checksum to verify source file and data "
        "transfer integrity. Assumed to be an MD5 checksum if "
        "--checksum-algorithm is not given."
    ),
)
@click.option(
    "--checksum-algorithm",
    default=None,
    show_default=True,
    help=("Specify an algorithm for --external-checksum or --verify-checksum"),
)
@click.option(
    "--exclude",
    multiple=True,
    show_default=True,
    help=(
        "Exclude files and directories found with names that match the given "
        "pattern in recursive transfers. Pattern may include * ? or [] for "
        "unix style globbing. Give this option multiple times to exclude "
        "multiple patterns."
    ),
)
@click.option("--perf-cc", type=int, hidden=True)
@click.option("--perf-p", type=int, hidden=True)
@click.option("--perf-pp", type=int, hidden=True)
@click.option("--perf-udt", is_flag=True, default=None, hidden=True)
@mutex_option_group("--recursive", "--external-checksum")
@LoginManager.requires_login("transfer")
def transfer_command(
    *,
    login_manager: LoginManager,
    batch: t.TextIO | None,
    sync_level: Literal["exists", "size", "mtime", "checksum"] | None,
    recursive: bool,
    source: tuple[uuid.UUID, str | None],
    destination: tuple[uuid.UUID, str | None],
    checksum_algorithm: str | None,
    external_checksum: str | None,
    skip_source_errors: bool,
    fail_on_quota_errors: bool,
    exclude: tuple[str, ...],
    label: str | None,
    preserve_timestamp: bool,
    verify_checksum: bool,
    encrypt_data: bool,
    submission_id: str | None,
    dry_run: bool,
    delete: bool,
    deadline: datetime.datetime | None,
    skip_activation_check: bool,
    notify: dict[str, bool],
    perf_cc: int | None,
    perf_p: int | None,
    perf_pp: int | None,
    perf_udt: bool | None,
) -> None:
    """
    Copy a file or directory from one endpoint to another as an asynchronous
    task.

    'globus transfer' has two modes. Single target, which transfers one
    file or one directory, and batch, which takes in several lines to transfer
    multiple files or directories. See "Batch Input" below for more information.

    'globus transfer' will always place the dest files in a
    consistent, deterministic location.  The contents of a source directory will
    be placed inside the dest directory.  A source file will be copied to
    the dest file path, which must not be an existing  directory.  All
    intermediate / parent directories on the dest will be automatically
    created if they don't exist.

    If the files or directories given as input are symbolic links, they are
    followed.  However, no other symbolic links are followed and no symbolic links
    are ever created on the dest.

    \b
    === Batched Input

    If you use `SOURCE_PATH` and `DEST_PATH` without the `--batch` flag, you
    will submit a single-file or single-directory transfer task.
    This has behavior similar to `cp` and `cp -r` across endpoints.

    Using `--batch`, `globus transfer` can submit a task which transfers multiple files
    or directories. The value for `--batch` can be a file to read from, or the
    character `-` which will read from stdin. From either the file or stdin, each line
    is treated as a path to a file or directory to transfer, respecting quotes.

    \b
    Lines are of the form
    [--recursive] [--external-checksum TEXT] SOURCE_PATH DEST_PATH\n

    Skips empty lines and allows comments beginning with "#".

    \b
    If you use `--batch` and a commandline SOURCE_PATH and/or DEST_PATH, these
    paths will be used as dir prefixes to any paths read from the batch source.

    \b
    === Sync Levels

    Sync Levels are ways to decide whether or not files are copied, with the
    following definitions:

    EXISTS: Determine whether or not to transfer based on file existence.
    If the destination file is absent, do the transfer.

    SIZE: Determine whether or not to transfer based on the size of the file.
    If destination file size does not match the source, do the transfer.

    MTIME: Determine whether or not to transfer based on modification times.
    If source has a newer modififed time than the destination, do the transfer.

    CHECKSUM: Determine whether or not to transfer based on checksums of file
    contents.
    If source and destination contents differ, as determined by a checksum of
    their contents, do the transfer.

    If a transfer fails, CHECKSUM must be used to restart the transfer.
    All other levels can lead to data corruption.

    {AUTOMATIC_ACTIVATION}
    """
    from globus_cli.services.transfer import add_batch_to_transfer_data, autoactivate

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

    if external_checksum and batch:
        raise click.UsageError(
            "You cannot use --external-checksum in addition to --batch. "
            "Instead, use --external-checksum on lines of --batch input "
            "which need it"
        )

    # the performance options (of which there are a few), have elements which should be
    # omitted in some cases
    # put them together before passing to TransferData
    perf_opts = {
        k: v
        for (k, v) in dict(
            perf_cc=perf_cc, perf_p=perf_p, perf_pp=perf_pp, perf_udt=perf_udt
        ).items()
        if v is not None
    }

    transfer_data = globus_sdk.TransferData(
        source_endpoint=source_endpoint,
        destination_endpoint=dest_endpoint,
        label=label,
        sync_level=sync_level,
        verify_checksum=verify_checksum,
        preserve_timestamp=preserve_timestamp,
        encrypt_data=encrypt_data,
        submission_id=submission_id,
        deadline=deadline,
        skip_source_errors=skip_source_errors,
        fail_on_quota_errors=fail_on_quota_errors,
        skip_activation_check=skip_activation_check,
        delete_destination_extra=delete,
        additional_fields={**perf_opts, **notify},
    )

    for exclude_name in exclude:
        transfer_data.add_filter_rule(exclude_name)

    if batch:
        add_batch_to_transfer_data(
            cmd_source_path, cmd_dest_path, checksum_algorithm, transfer_data, batch
        )
    else:
        if cmd_source_path is None or cmd_dest_path is None:
            raise click.UsageError(
                "transfer requires either SOURCE_PATH and DEST_PATH or --batch"
            )
        transfer_data.add_item(
            cmd_source_path,
            cmd_dest_path,
            external_checksum=external_checksum,
            checksum_algorithm=checksum_algorithm,
            recursive=recursive,
        )

    for item in transfer_data["DATA"]:
        if item["recursive"]:
            has_recursive_items = True
            break
    else:
        has_recursive_items = False

    if exclude and not has_recursive_items:
        raise click.UsageError("--exclude can only be used with --recursive transfers")

    if dry_run:
        display(
            transfer_data.data,
            response_key="DATA",
            fields=[
                Field("Source Path", "source_path"),
                Field("Dest Path", "destination_path"),
                Field("Recursive", "recursive"),
                Field("External Checksum", "external_checksum"),
            ],
        )
        # exit safely
        return

    # autoactivate after parsing all args and putting things together
    # skip this if skip-activation-check is given
    if not skip_activation_check:
        autoactivate(transfer_client, source_endpoint, if_expires_in=60)
        autoactivate(transfer_client, dest_endpoint, if_expires_in=60)

    res = transfer_client.submit_transfer(transfer_data)
    display(
        res,
        text_mode=TextMode.text_record,
        fields=[Field("Message", "message"), Field("Task ID", "task_id")],
    )
