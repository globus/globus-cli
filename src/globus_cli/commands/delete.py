from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli import utils
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import (
    ENDPOINT_PLUS_OPTPATH,
    TaskPath,
    command,
    delete_and_rm_options,
    local_user_option,
    task_submission_options,
)
from globus_cli.termio import Field, display, err_is_terminal, term_is_interactive
from globus_cli.utils import make_dict_json_serializable


@command(
    "delete",
    short_help="Submit a delete task (asynchronous).",
    adoc_examples="""Delete a single file.

[source,bash]
----
$ ep_id=313ce13e-b597-5858-ae13-29e46fea26e6
$ globus delete $ep_id:~/myfile.txt
----

Delete a directory recursively.

[source,bash]
----
$ ep_id=313ce13e-b597-5858-ae13-29e46fea26e6
$ globus delete $ep_id:~/mydir --recursive
----

Use the batch input method to transfer multiple files and or dirs.

[source,bash]
----
$ ep_id=313ce13e-b597-5858-ae13-29e46fea26e6
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
$ ep_id=313ce13e-b597-5858-ae13-29e46fea26e6
$ task_id="$(globus delete $ep_id:~/mydir --recursive \
    --jmespath 'task_id' --format unix)"
$ echo "Waiting on $task_id"
$ globus task wait "$task_id"
----
""",
)
@task_submission_options
@delete_and_rm_options()
@local_user_option
@click.argument("endpoint_plus_path", type=ENDPOINT_PLUS_OPTPATH)
@LoginManager.requires_login("transfer")
def delete_command(
    login_manager: LoginManager,
    *,
    batch: t.TextIO | None,
    ignore_missing: bool,
    star_silent: bool,
    recursive: bool | globus_sdk.MissingType,
    enable_globs: bool,
    endpoint_plus_path: tuple[uuid.UUID, str | None],
    label: str | globus_sdk.MissingType,
    submission_id: str | globus_sdk.MissingType,
    dry_run: bool,
    deadline: str | globus_sdk.MissingType,
    skip_activation_check: bool,
    notify: dict[str, bool],
    local_user: str | globus_sdk.MissingType,
) -> None:
    """
    Submits an asynchronous task that deletes files and/or directories on the target
    endpoint.

    *globus delete* has two modes. Single target, which deletes one
    file or one directory, and batch, which takes in several lines to delete
    multiple files or directories. See "Batch Input" below for more information.

    Symbolic links are never followed - only unlinked (deleted).

    === Batch Input

    If you give a PATH without the `--batch` flag, you will submit a
    single-file or single-directory delete task.

    Using `--batch`, `globus delete` can submit a task which deletes multiple files or
    directories.
    Each line of `--batch` input is treated as a path to a file or directory to delete.

    \b
    Lines are of the form
      PATH

    Note that unlike `globus transfer`, `--recursive` is not an option at the per-line
    level, instead, if given with the original command, all paths that point to
    directories will be recursively deleted.

    Empty lines and comments beginning with '#' are ignored.

    \b
    If you use `--batch` and supply a PATH via the commandline, the commandline PATH is
    treated as a prefix to all of the paths read from the `--batch` input.
    """
    endpoint_id, path = endpoint_plus_path
    transfer_client = login_manager.get_transfer_client()

    delete_data = globus_sdk.DeleteData(
        endpoint_id,
        label=label,
        recursive=recursive,
        submission_id=submission_id,
        deadline=deadline,
        local_user=local_user,
        additional_fields={
            "ignore_missing": ignore_missing,
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
        def process_batch_line(path: TaskPath) -> None:
            """
            Parse a line of batch input and add it to the delete submission
            item.
            """
            delete_data.add_item(str(path))

        utils.shlex_process_stream(process_batch_line, batch, "--batch")
    else:
        if path is None:
            raise click.UsageError("delete requires either a PATH OR --batch")

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
        display(
            make_dict_json_serializable(delete_data),
            response_key="DATA",
            fields=[Field("Path", "path")],
        )
        # exit safely
        return

    res = transfer_client.submit_delete(delete_data)
    display(
        res,
        text_mode=display.RECORD,
        fields=[Field("Message", "message"), Field("Task ID", "task_id")],
    )
