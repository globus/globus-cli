from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    OMITTABLE_INT,
    OMITTABLE_STRING,
    command,
    encrypt_data_option,
    fail_on_quota_errors_option,
    filter_rule_options,
    mutex_option_group,
    preserve_timestamp_option,
    skip_source_errors_option,
    sync_level_option,
    task_submission_options,
    transfer_batch_option,
    transfer_recursive_option,
    verify_checksum_option,
)
from globus_cli.termio import Field, display


@command(
    "transfer",
    # the order of filter_rules determines behavior, so we need to combine
    # include and exclude options during argument parsing to preserve their ordering
    opts_to_combine={
        "include": "filter_rules",
        "exclude": "filter_rules",
    },
    short_help="Submit a transfer task (asynchronous).",
    adoc_examples="""Transfer a single file:

[source,bash]
----
$ source_ep=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ dest_ep=313ce13e-b597-5858-ae13-29e46fea26e6
$ globus transfer $source_ep:/share/godata/file1.txt $dest_ep:~/mynewfile.txt
----

Transfer a directory recursively:

[source,bash]
----
$ source_ep=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ dest_ep=313ce13e-b597-5858-ae13-29e46fea26e6
$ globus transfer $source_ep:/share/godata/ $dest_ep:~/mynewdir/ --recursive
----

Use the batch input method to transfer multiple files and directories:

[source,bash]
----
$ source_ep=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ dest_ep=313ce13e-b597-5858-ae13-29e46fea26e6
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
$ source_ep=aa752cea-8222-5bc8-acd9-555b090c0ccb
$ dest_ep=313ce13e-b597-5858-ae13-29e46fea26e6
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
source_ep=aa752cea-8222-5bc8-acd9-555b090c0ccb
dest_ep=313ce13e-b597-5858-ae13-29e46fea26e6

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
@filter_rule_options
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
@click.option(
    "--external-checksum",
    help=(
        "An external checksum to verify source file and data "
        "transfer integrity. Assumed to be an MD5 checksum if "
        "--checksum-algorithm is not given."
    ),
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option(
    "--checksum-algorithm",
    help="Specify an algorithm for --external-checksum or --verify-checksum",
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option(
    "--source-local-user",
    help=(
        "Optional value passed to the source's identity mapping specifying which local "
        "user account to map to. Only usable with Globus Connect Server v5 mapped "
        "collections."
    ),
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option(
    "--destination-local-user",
    help=(
        "Optional value passed to the destination's identity mapping specifying which "
        "local user account to map to. Only usable with Globus Connect Server v5 "
        "mapped collections."
    ),
    default=globus_sdk.MISSING,
    type=OMITTABLE_STRING,
)
@click.option("--perf-cc", default=globus_sdk.MISSING, type=OMITTABLE_INT, hidden=True)
@click.option("--perf-p", default=globus_sdk.MISSING, type=OMITTABLE_INT, hidden=True)
@click.option("--perf-pp", default=globus_sdk.MISSING, type=OMITTABLE_INT, hidden=True)
@click.option("--perf-udt", is_flag=True, hidden=True)
@mutex_option_group("--recursive", "--external-checksum")
@LoginManager.requires_login("transfer")
def transfer_command(
    login_manager: LoginManager,
    *,
    batch: t.TextIO | None,
    sync_level: (
        t.Literal["exists", "size", "mtime", "checksum"] | globus_sdk.MissingType
    ),
    recursive: bool | globus_sdk.MissingType,
    source: tuple[uuid.UUID, str | None],
    destination: tuple[uuid.UUID, str | None],
    checksum_algorithm: str | globus_sdk.MissingType,
    external_checksum: str | globus_sdk.MissingType,
    skip_source_errors: bool,
    fail_on_quota_errors: bool,
    filter_rules: list[tuple[t.Literal["include", "exclude"], str]],
    label: str | globus_sdk.MissingType,
    preserve_timestamp: bool,
    verify_checksum: bool,
    encrypt_data: bool,
    submission_id: str | globus_sdk.MissingType,
    dry_run: bool,
    delete: bool,
    delete_destination_extra: bool,
    deadline: str | globus_sdk.MissingType,
    skip_activation_check: bool,
    notify: dict[str, bool],
    perf_cc: int | globus_sdk.MissingType,
    perf_p: int | globus_sdk.MissingType,
    perf_pp: int | globus_sdk.MissingType,
    perf_udt: bool,
    source_local_user: str | globus_sdk.MissingType,
    destination_local_user: str | globus_sdk.MissingType,
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
    === Batch Input

    If you use `SOURCE_PATH` and `DEST_PATH` without the `--batch` flag, you
    will submit a single-file or single-directory transfer task.

    Using `--batch`, `globus transfer` can submit a task which transfers multiple
    specified files or directories.
    Each line of `--batch` input is treated as a path to a file or directory to
    transfer.

    \b
    Lines are of the form
    [--recursive] [--external-checksum TEXT] SOURCE_PATH DEST_PATH\n

    Each line of the batch input is parsed like it would be at the command line.
    This means that if `SOURCE_PATH` or `DEST_PATH` contain spaces,
    the path should be wrapped in quotes, or the spaces should be escaped
    using a backslash character ("\\").

    Similarly, empty lines are skipped, and comments beginning with "#" are allowed.

    \b
    If you use `--batch` and a commandline SOURCE_PATH and/or DEST_PATH, these
    paths will be used as dir prefixes to any paths read from the `--batch` input.

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

    \b
    === Include and Exclude

    The `--include` and `--exclude` options are evaluated in order together
    to determine which files are transferred during recursive transfers.
    Earlier `--include` and `--exclude` options have priority over later such
    options, with the first option that matches the name of a file being
    applied. A file that does not match any `--include` or `--exclude` options
    is included by default, making the `--include` option only useful for
    overriding later `--exclude` options.

    For example, `globus transfer --include "*.txt" --exclude "*" ...` will
    only transfer files ending in .txt found within the directory structure.
    """
    from globus_cli.services.transfer import add_batch_to_transfer_data

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
    if external_checksum and batch:
        raise click.UsageError(
            "You cannot use `--external-checksum` in addition to `--batch`. "
            "Instead, use `--external-checksum` on lines of `--batch` input which "
            "need it."
        )

    # the performance options (of which there are a few), have elements which should be
    # omitted in some cases
    # put them together before passing to TransferData
    perf_opts = {
        k: v
        for (k, v) in (
            ("perf_cc", perf_cc),
            ("perf_p", perf_p),
            ("perf_pp", perf_pp),
            ("perf_udt", True if perf_udt else globus_sdk.MISSING),
        )
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
        delete_destination_extra=(delete or delete_destination_extra),
        source_local_user=source_local_user,
        destination_local_user=destination_local_user,
        additional_fields={**perf_opts, **notify},
    )

    for rule in filter_rules:
        method, name = rule
        transfer_data.add_filter_rule(method=method, name=name, type="file")

    if batch:
        add_batch_to_transfer_data(
            cmd_source_path, cmd_dest_path, checksum_algorithm, transfer_data, batch
        )
    else:
        if cmd_source_path is None or cmd_dest_path is None:
            raise click.UsageError(
                "Transfer requires either `SOURCE_PATH` and `DEST_PATH` or `--batch`"
            )
        transfer_data.add_item(
            cmd_source_path,
            cmd_dest_path,
            external_checksum=external_checksum,
            checksum_algorithm=checksum_algorithm,
            recursive=recursive,
        )

    for item in transfer_data["DATA"]:
        if item.get("recursive"):
            has_recursive_items = True
            break
    else:
        has_recursive_items = False

    if filter_rules and not has_recursive_items:
        raise click.UsageError(
            "`--include` and `--exclude` can only be used with `--recursive` transfers"
        )

    if dry_run:
        display(
            transfer_data,
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

    res = transfer_client.submit_transfer(transfer_data)
    display(
        res,
        text_mode=display.RECORD,
        fields=[Field("Message", "message"), Field("Task ID", "task_id")],
    )
