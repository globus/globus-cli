import click
import globus_sdk

from globus_cli import utils
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TaskPath,
    command,
    delete_and_rm_options,
    task_submission_options,
)
from globus_cli.termio import (
    Field,
    TextMode,
    display,
    err_is_terminal,
    term_is_interactive,
)


@command(
    "delete",
    short_help="Submit a delete task (asynchronous)",
    adoc_examples="""Delete a single file.

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus delete $ep_id:~/myfile.txt
----

Delete a directory recursively.

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus delete $ep_id:~/mydir --recursive
----

Use the batch input method to transfer multiple files and or dirs.

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ globus delete $ep_id --batch - --recursive
~/myfile1.txt
~/myfile2.txt
~/myfile3.txt
~/mygodatadir
<EOF>
----

Submit a deletion task and get back the task ID for use in `globus task wait`:

[source,bash]
----
$ ep_id=ddb59af0-6d04-11e5-ba46-22000b92c6ec
$ task_id="$(globus delete $ep_id:~/mydir --recursive \
    --jmespath 'task_id' --format unix)"
$ echo "Waiting on $task_id"
$ globus task wait "$task_id"
----
""",
)
@task_submission_options
@delete_and_rm_options
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_OPTPATH)
@LoginManager.requires_login("transfer")
def delete_command(
    *,
    login_manager: LoginManager,
    batch,
    ignore_missing,
    star_silent,
    recursive,
    enable_globs,
    endpoint_plus_path,
    label,
    submission_id,
    dry_run,
    deadline,
    skip_activation_check,
    notify,
):
    """
    Submits an asynchronous task that deletes files and/or directories on the target
    endpoint.

    *globus delete* has two modes. Single target, which deletes one
    file or one directory, and batch, which takes in several lines to delete
    multiple files or directories. See "Batch Input" below for more information.

    Symbolic links are never followed - only unlinked (deleted).

    === Batch Input

    If you give a SOURCE_PATH without the --batch flag, you will submit a
    single-file or single-directory delete task. This has
    behavior similar to `rm` and `rm -r`, across endpoints.

    Using `--batch`, *globus delete* can submit a task which deletes multiple files or
    directories. The value for `--batch` can be a file to read from, or the character
    `-` which will read from stdin. From either the file or stdin, each line is treated
    as a path to a file or directory to delete, respecting quotes.

    \b
    Lines are of the form
      PATH

    Note that unlike 'globus transfer' --recursive is not an option at the per line
    level, instead, if given with the original command, all paths that point to
    directories will be recursively deleted.

    Empty lines and comments beginning with '#' are ignored.

    Batch only requires an ENDPOINT on the "base" command, but you may pass an
    ENPDOINT:PATH to prefix all the paths read in the batch with that path.

    {AUTOMATIC_ACTIVATION}
    """
    from globus_cli.services.transfer import autoactivate

    endpoint_id, path = endpoint_plus_path
    if path is None and (not batch):
        raise click.UsageError("delete requires either a PATH OR --batch")

    transfer_client = login_manager.get_transfer_client()

    # attempt to activate unless --skip-activation-check is given
    if not skip_activation_check:
        autoactivate(transfer_client, endpoint_id, if_expires_in=60)

    delete_data = globus_sdk.DeleteData(
        transfer_client,
        endpoint_id,
        label=label,
        recursive=recursive,
        submission_id=submission_id,
        deadline=deadline,
        additional_fields={
            "ignore_missing": ignore_missing,
            "skip_activation_check": skip_activation_check,
            "interpret_globs": enable_globs,
            **notify,
        },
    )

    if batch:
        # although this sophisticated structure (like that in transfer)
        # isn't strictly necessary, it gives us the ability to add options in
        # the future to these lines with trivial modifications
        @click.command()
        @click.argument("path", type=TaskPath(base_dir=path))
        def process_batch_line(path):
            """
            Parse a line of batch input and add it to the delete submission
            item.
            """
            delete_data.add_item(str(path))

        utils.shlex_process_stream(process_batch_line, batch, "--batch")
    else:
        if not star_silent and enable_globs and path.endswith("*"):
            # not intuitive, but `click.confirm(abort=True)` prints to stdout
            # unnecessarily, which we don't really want...
            # only do this check if stderr is a pty
            if (
                err_is_terminal()
                and term_is_interactive()
                and not click.confirm(
                    'Are you sure you want to delete all files matching "{}"?'.format(
                        path
                    ),
                    err=True,
                )
            ):
                click.echo("Aborted.", err=True)
                click.get_current_context().exit(1)
        delete_data.add_item(path)

    if dry_run:
        display(delete_data.data, response_key="DATA", fields=[Field("Path", "path")])
        # exit safely
        return

    res = transfer_client.submit_delete(delete_data)
    display(
        res,
        text_mode=TextMode.text_record,
        fields=[Field("Message", "message"), Field("Task ID", "task_id")],
    )
