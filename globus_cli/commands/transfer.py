import click

from globus_sdk import TransferData

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, task_submission_options,
    TaskPath, shlex_process_stdin, endpoint_plus_path_options,
    parse_source_and_dest_endpoint_plus_path)
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RECORD

from globus_cli.services.transfer import get_client, autoactivate


@click.command('transfer', short_help='Submit a transfer task',
               help=("""\
    Copy a file or directory from one endpoint to another as an asynchronous
    task.

    \b
    Batched Input
    ===

    If you use `SOURCE_PATH` and `DEST_PATH` without the `--batch` flag, you
    will submit a single-file or single-directory transfer task.
    This has behavior similar to `cp` and `cp -r`, across endpoints of course.

    Using `--batch`, `globus transfer` can submit a task which transfers
    multiple files or directories. Paths to transfer are taken from stdin.
    Lines are split on spaces, respecting quotes, and every line is treated as
    a file or directory to transfer.

    \b
    Lines are of the form
    [--recursive] SOURCE_PATH DEST_PATH

    Skips empty lines and allows comments beginning with "#".

    \b
    If you use `--batch` and a commandline SOURCE_PATH and/or DEST_PATH, these
    paths will be used as dir prefixes to any paths on stdin.

    \b
    Sync Levels
    ===

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
    """))
@common_options
@task_submission_options
@click.option('--recursive', '-r', is_flag=True,
              help=('SOURCE_PATH and DEST_PATH are both directories, do a '
                    'recursive dir transfer'))
@click.option('--sync-level', '-s', default=None, show_default=True,
              type=CaseInsensitiveChoice(
                  ("exists", "size", "mtime", "checksum")),
              help=('How will the Transfer task determine whether or not to '
                    'actually transfer a file over the network?'))
@click.option('--preserve-mtime', is_flag=True, default=False,
              help=('Preserve file and directory modification times.'))
@click.option('--verify-checksum/--no-verify-checksum', default=True,
              show_default=True,
              help=('Verify checksum after transfer.'))
@click.option('--encrypt', is_flag=True, default=False,
              help=('Encrypt data sent through the network.'))
@click.option('--delete', is_flag=True, default=False,
              help=('Delete extraneous files in the destination directory. '
                    'Only applies to recursive directory transfers.'))
@click.option('--batch', is_flag=True,
              help=('Accept a batch of source/dest path pairs on stdin (i.e. '
                    'run in batchmode). '
                    'Uses SOURCE_ENDPOINT_ID and DEST_ENDPOINT_ID as passed '
                    'on the commandline. Commandline paths are still allowed '
                    'and are used as prefixes to the batchmode inputs.'))
@endpoint_plus_path_options(path_required=False, prefix="source")
@endpoint_plus_path_options(path_required=False, prefix="destination")
def transfer_command(batch, sync_level, recursive, label,
                     source_endpoint_plus_path, source_bookmark,
                     destination_endpoint_plus_path, destination_bookmark,
                     preserve_mtime, verify_checksum, encrypt, submission_id,
                     dry_run, delete, deadline):
    """
    Executor for `globus transfer`
    """
    source_endpoint, cmd_source_path, dest_endpoint, cmd_dest_path = (
        parse_source_and_dest_endpoint_plus_path(
            source_endpoint_plus_path, source_bookmark,
            destination_endpoint_plus_path, destination_bookmark))

    if recursive and batch:
        raise click.UsageError(
            ('You cannot use --recursive in addition to --batch. '
             'Instead, use --recursive on lines of --batch input '
             'which need it'))

    if (cmd_source_path is None or cmd_dest_path is None) and (not batch):
        raise click.UsageError(
            ('transfer requires either SOURCE_PATH and DEST_PATH or '
             '--batch'))

    client = get_client()
    transfer_data = TransferData(
        client, source_endpoint, dest_endpoint,
        label=label, sync_level=sync_level, verify_checksum=verify_checksum,
        preserve_timestamp=preserve_mtime, encrypt_data=encrypt,
        submission_id=submission_id, delete_destination_extra=delete,
        deadline=deadline)

    if batch:
        @click.command()
        @click.option('--recursive', '-r', is_flag=True)
        @click.argument('source_path', type=TaskPath(base_dir=cmd_source_path))
        @click.argument('dest_path', type=TaskPath(base_dir=cmd_dest_path))
        def process_batch_line(dest_path, source_path, recursive):
            """
            Parse a line of batch input and turn it into a transfer submission
            item.
            """
            transfer_data.add_item(str(source_path), str(dest_path),
                                   recursive=recursive)

        shlex_process_stdin(
            process_batch_line,
            ('Enter transfers, line by line, as\n\n'
             '    [--recursive] SOURCE_PATH DEST_PATH\n'))
    else:
        transfer_data.add_item(cmd_source_path, cmd_dest_path,
                               recursive=recursive)

    if dry_run:
        formatted_print(
            transfer_data, response_key='DATA',
            fields=(('Source Path', 'source_path'),
                    ('Dest Path', 'destination_path'),
                    ('Recursive', 'recursive')))
        # exit safely
        return

    # autoactivate after parsing all args and putting things together
    autoactivate(client, source_endpoint, if_expires_in=60)
    autoactivate(client, dest_endpoint, if_expires_in=60)

    res = client.submit_transfer(transfer_data)
    formatted_print(res, text_format=FORMAT_TEXT_RECORD,
                    fields=(('Message', 'message'), ('Task ID', 'task_id')))
