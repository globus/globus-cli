from __future__ import annotations

import click
from globus_sdk import TransferData

from globus_cli import utils
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TaskPath,
    command,
    mutex_option_group,
    task_submission_options,
)
from globus_cli.services.transfer import autoactivate
from globus_cli.termio import FORMAT_TEXT_RECORD, formatted_print


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
@task_submission_options
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="SOURCE_PATH and DEST_PATH are both directories, do a recursive dir transfer",
)
@click.option(
    "--sync-level",
    "-s",
    default=None,
    show_default=True,
    type=click.Choice(("exists", "size", "mtime", "checksum"), case_sensitive=False),
    help=(
        "How will the Transfer task determine whether or not to "
        "actually transfer a file over the network?"
    ),
)
@click.option(
    "--preserve-mtime",
    is_flag=True,
    default=False,
    help="Preserve file and directory modification times.",
)
@click.option(
    "--verify-checksum/--no-verify-checksum",
    default=True,
    show_default=True,
    help="Verify checksum after transfer.",
)
@click.option(
    "--encrypt",
    is_flag=True,
    default=False,
    help="Encrypt data sent through the network.",
)
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
    "--batch",
    type=click.File("r"),
    help=(
        "Accept a batch of source/dest path pairs from a file. Use the special `-` "
        "value to read from stdin; otherwise opens the file from the argument and "
        "passes through lines from that file. Uses SOURCE_ENDPOINT_ID and "
        "DEST_ENDPOINT_ID as passed on the commandline. Commandline paths are still "
        "allowed and are used as prefixes to the batchmode inputs."
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
    "--skip-source-errors",
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        "Skip over source paths that hit permission denied or file not "
        "found errors during the transfer."
    ),
)
@click.option(
    "--fail-on-quota-errors",
    is_flag=True,
    default=False,
    show_default=True,
    help=(
        "Cause the task to fail if any quota exceeded errors are hit "
        "during the transfer."
    ),
)
@click.option(
    "--exclude",
    multiple=True,
    default=None,
    show_default=True,
    help=(
        "Exclude files and directories found with names that match the given "
        "pattern in recursive transfers. Pattern may include * ? or [] for "
        "unix style globbing. Give this option multiple times to exclude "
        "multiple patterns."
    ),
)
@click.argument(
    "source", metavar="SOURCE_ENDPOINT_ID[:SOURCE_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@click.argument(
    "destination", metavar="DEST_ENDPOINT_ID[:DEST_PATH]", type=ENDPOINT_PLUS_OPTPATH
)
@click.option("--perf-cc", type=int, hidden=True)
@click.option("--perf-p", type=int, hidden=True)
@click.option("--perf-pp", type=int, hidden=True)
@click.option("--perf-udt", is_flag=True, default=None, hidden=True)
@mutex_option_group("--recursive", "--external-checksum")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def transfer_command(
    *,
    login_manager: LoginManager,
    batch,
    sync_level,
    recursive,
    destination,
    source,
    checksum_algorithm,
    external_checksum,
    skip_source_errors,
    fail_on_quota_errors,
    exclude,
    label,
    preserve_mtime,
    verify_checksum,
    encrypt,
    submission_id,
    dry_run,
    delete,
    deadline,
    skip_activation_check,
    notify,
    perf_cc,
    perf_p,
    perf_pp,
    perf_udt,
):
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
    is treated as a path to a file or directory to delete, respecting quotes.

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
    source_endpoint, cmd_source_path = source
    dest_endpoint, cmd_dest_path = destination

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

    if (cmd_source_path is None or cmd_dest_path is None) and (not batch):
        raise click.UsageError(
            "transfer requires either SOURCE_PATH and DEST_PATH or --batch"
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

    def _make_exclude_rule(name_pattern):
        return {"DATA_TYPE": "filter_rule", "method": "exclude", "name": name_pattern}

    if exclude:
        filter_rules: list[str] | None = [_make_exclude_rule(s) for s in exclude]
    else:
        filter_rules = None

    transfer_client = login_manager.get_transfer_client()
    transfer_data = TransferData(
        transfer_client,
        source_endpoint,
        dest_endpoint,
        label=label,
        sync_level=sync_level,
        verify_checksum=verify_checksum,
        preserve_timestamp=preserve_mtime,
        encrypt_data=encrypt,
        submission_id=submission_id,
        deadline=deadline,
        skip_source_errors=skip_source_errors,
        fail_on_quota_errors=fail_on_quota_errors,
        additional_fields={
            "delete_destination_extra": delete,
            "skip_activation_check": skip_activation_check,
            "filter_rules": filter_rules,
            **notify,
            **perf_opts,
        },
    )

    if batch:

        @click.command()
        @click.option("--external-checksum")
        @click.option("--recursive", "-r", is_flag=True)
        @click.argument("source_path", type=TaskPath(base_dir=cmd_source_path))
        @click.argument("dest_path", type=TaskPath(base_dir=cmd_dest_path))
        @mutex_option_group("--recursive", "--external-checksum")
        def process_batch_line(dest_path, source_path, recursive, external_checksum):
            """
            Parse a line of batch input and turn it into a transfer submission
            item.
            """
            transfer_data.add_item(
                str(source_path),
                str(dest_path),
                external_checksum=external_checksum,
                checksum_algorithm=checksum_algorithm,
                recursive=recursive,
            )

        utils.shlex_process_stream(process_batch_line, batch)

    else:
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
        formatted_print(
            transfer_data.data,
            response_key="DATA",
            fields=(
                ("Source Path", "source_path"),
                ("Dest Path", "destination_path"),
                ("Recursive", "recursive"),
                ("External Checksum", "external_checksum"),
            ),
        )
        # exit safely
        return

    # autoactivate after parsing all args and putting things together
    # skip this if skip-activation-check is given
    if not skip_activation_check:
        autoactivate(transfer_client, source_endpoint, if_expires_in=60)
        autoactivate(transfer_client, dest_endpoint, if_expires_in=60)

    res = transfer_client.submit_transfer(transfer_data)
    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=(("Message", "message"), ("Task ID", "task_id")),
    )
