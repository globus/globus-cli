import click

from globus_sdk import DeleteData


from globus_cli.parsing import (
    common_options, task_submission_options, TaskPath, shlex_process_stdin,
    endpoint_plus_path_options, parse_endpoint_plus_path)
from globus_cli.safeio import formatted_print, FORMAT_TEXT_RECORD

from globus_cli.services.transfer import get_client, autoactivate


@click.command('delete', short_help='Submit a delete task',
               help=('Delete a file or directory from one endpoint as an '
                     'asynchronous task.'))
@common_options
@task_submission_options
@click.option(
    '--recursive', '-r', is_flag=True, help='Recursively delete dirs')
@click.option('--ignore-missing', '-f', is_flag=True,
              help="Don't throw errors if the file or dir is absent")
@click.option('--batch', is_flag=True,
              help=('Accept a batch of paths on stdin (i.e. run in '
                    'batchmode). Uses ENDPOINT_ID as passed on the '
                    'commandline. Any commandline PATH given will be used as '
                    'a prefix to all paths given'))
@endpoint_plus_path_options(path_required=False)
def delete_command(batch, ignore_missing, recursive, endpoint_plus_path,
                   bookmark, label, submission_id, dry_run, deadline):
    """
    Executor for `globus delete`
    """
    endpoint_id, path = parse_endpoint_plus_path(
        endpoint_plus_path, bookmark, path_required=False)

    if path is None and (not batch):
        raise click.UsageError(
            'delete requires either a PATH OR --batch')

    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    delete_data = DeleteData(client, endpoint_id,
                             label=label,
                             recursive=recursive,
                             ignore_missing=ignore_missing,
                             submission_id=submission_id,
                             deadline=deadline)

    if batch:
        # although this sophisticated structure (like that in transfer)
        # isn't strictly necessary, it gives us the ability to add options in
        # the future to these lines with trivial modifications
        @click.command()
        @click.argument('path', type=TaskPath(base_dir=path))
        def process_batch_line(path):
            """
            Parse a line of batch input and add it to the delete submission
            item.
            """
            delete_data.add_item(str(path))

        shlex_process_stdin(
            process_batch_line, 'Enter paths to delete, line by line.')
    else:
        delete_data.add_item(path)

    if dry_run:
        formatted_print(delete_data, response_key='DATA',
                        fields=[('Path', 'path')])
        # exit safely
        return

    res = client.submit_delete(delete_data)
    formatted_print(res, text_format=FORMAT_TEXT_RECORD,
                    fields=(('Message', 'message'), ('Task ID', 'task_id')))
