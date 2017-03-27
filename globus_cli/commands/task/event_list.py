import click

from globus_cli.parsing import common_options, task_id_arg
from globus_cli.safeio import OutputFormatter

from globus_cli.services.transfer import iterable_response_to_dict, get_client


@click.command('event-list', help='List Events for a given Task')
@common_options
@task_id_arg
@click.option(
    "--limit", default=10, show_default=True, help="Limit number of results.")
@click.option(
    "--filter-errors", is_flag=True, help="Filter results to errors")
@click.option(
    "--filter-non-errors", is_flag=True, help="Filter results to non errors")
def task_event_list(task_id, limit, filter_errors, filter_non_errors):
    """
    Executor for `globus task-event-list`
    """
    client = get_client()

    # set filter based on filter flags, if both set do nothing
    filter_string = None
    if filter_errors and not filter_non_errors:
        filter_string = "is_error:1"
    if filter_non_errors and not filter_errors:
        filter_string = "is_error:1"

    event_iterator = client.task_event_list(
        task_id, num_results=limit, filter=filter_string)

    OutputFormatter(fields=(('Time', 'time'), ('Code', 'code'),
                            ('Is Error', 'is_error'), ('Details', 'details'))
                    ).print_response(
        event_iterator, json_converter=iterable_response_to_dict)
