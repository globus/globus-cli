import click

from globus_sdk import DeleteData


from globus_cli.parsing import (
    common_options, task_submission_options, ENDPOINT_PLUS_REQPATH)
from globus_cli.safeio import (
    formatted_print, FORMAT_TEXT_RECORD, FORMAT_SILENT)
from globus_cli.helpers import is_verbose
from globus_cli.services.transfer import get_client, autoactivate


@click.command("rm", short_help="Remove files or directories",
               help=("Remove a file or directory from an endpoint as a "
                     "synchronous task. Similar to `globus delete`, but waits "
                     "for the delete task to finish before exiting. "
                     "Allows for bash style globbing with `*`, `?`, `[`, and "
                     "`]`."))
@common_options
@task_submission_options
@click.option(
    "--recursive", "-r", is_flag=True, help="Recursively remove dirs")
@click.option("--ignore-missing", "-f", is_flag=True,
              help="Don't throw errors if the file or dir is absent")
@click.argument("endpoint_plus_path", metavar=ENDPOINT_PLUS_REQPATH.metavar,
                type=ENDPOINT_PLUS_REQPATH)
@click.option(
    "--timeout", type=int, metavar="N", default=60, show_default=True,
    help=("If the delete task does not terminate after N seconds, this command"
          " will exit with code 1. The task will continue to exist and may "
          "finish in the background."))
def rm_command(ignore_missing, recursive, endpoint_plus_path,
               label, submission_id, dry_run, deadline, timeout):
    """
    Executor for `globus rm`
    """
    endpoint_id, path = endpoint_plus_path

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    delete_data = DeleteData(client, endpoint_id,
                             label=label,
                             recursive=recursive,
                             ignore_missing=ignore_missing,
                             submission_id=submission_id,
                             deadline=deadline,
                             interpret_globs=True)
    delete_data.add_item(path)

    if dry_run:
        formatted_print(delete_data, response_key="DATA",
                        fields=[("Path", "path")])
        # exit safely
        return

    # submit task, wait for it to finish or timeout, then get task information
    task_id = client.submit_delete(delete_data)["task_id"]
    client.task_wait(task_id, timeout=timeout, polling_interval=1)
    res = client.get_task(task_id)

    # exit 0 if success
    if res["status"] == "SUCCEEDED":
        if is_verbose():
            formatted_print(res, text_format=FORMAT_TEXT_RECORD,
                            fields=(("Status", "status"),
                                    ("Task ID", "task_id")))
        else:
            formatted_print(res, text_format=FORMAT_SILENT)

    # exit 1 if failed, and give some details for why
    elif res["status"] == "FAILED":
        details = client.task_event_list(
            task_id, filter="is_error:1")[0]["details"]
        formatted_print(res, simple_text=("Task failed with "
                                          "details: {}.".format(details)))
        click.get_current_context().exit(1)

    # exit 1 if timeout
    else:
        formatted_print(res, simple_text=("Task has yet to complete after {}"
                                          " seconds.".format(timeout)))
        click.get_current_context().exit(1)
