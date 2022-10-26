from __future__ import annotations

import json
import typing as t
import uuid

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import Field, display, formatters
from globus_cli.utils import PagingWrapper

from ._common import task_id_arg


class SquashedJsonFormatter(formatters.FieldFormatter[t.Tuple[t.Any, bool]]):
    def parse(self, value: t.Any) -> tuple[t.Any, bool]:
        if not isinstance(value, str):
            raise ValueError("bad input data")

        is_json = False
        try:
            loaded = json.loads(value)
            is_json = True
        except ValueError:
            loaded = value

        return (loaded, is_json)

    def render(self, value: tuple[t.Any, bool]) -> str:
        data, is_json = value
        if is_json:
            return json.dumps(data, separators=(",", ":"), sort_keys=True)
        else:
            return str(data.replace("\n", "\\n"))


@command(
    "event-list",
    short_help="List events for a given task",
    adoc_synopsis="""
`globus task event-list [OPTIONS] TASK_ID`

`globus task event-list --filter-errors [OPTIONS] TASK_ID`

`globus task event-list --filter-non-errors [OPTIONS] TASK_ID`
""",
    adoc_output="""When output is in text mode, the following fields are used:

- 'Time'
- 'Code'
- 'Is Error'
- 'Details'
""",
    adoc_examples="""Show why a task is paused, producing JSON output:

[source,bash]
----
$ globus task pause-info TASK_ID --format JSON
----
""",
)
@task_id_arg
@click.option(
    "--limit", type=int, default=10, show_default=True, help="Limit number of results."
)
@click.option("--filter-errors", is_flag=True, help="Filter results to errors")
@click.option("--filter-non-errors", is_flag=True, help="Filter results to non errors")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def task_event_list(
    *,
    login_manager: LoginManager,
    task_id: uuid.UUID,
    limit: int,
    filter_errors: bool,
    filter_non_errors: bool,
):
    """
    This command shows the recent events for a running task.
    Most events of interest are fault events, which are errors which occurred on an
    endpoint but which are non-fatal to a task. For example, Permission Denied errors
    on an endpoint don't cancel the task because they are often resolvable -- at which
    point the task would retry succeed.

    Events may be filtered using '--filter-errors' or '--filter-non-errors', but
    these two options may not be used in tandem.

    NOTE: Tasks older than one month may no longer have event log history. In this
    case, no events will be shown.
    """
    from globus_cli.services.transfer import iterable_response_to_dict

    transfer_client = login_manager.get_transfer_client()

    # cannot filter by both errors and non errors
    if filter_errors and filter_non_errors:
        raise click.UsageError("Cannot filter by both errors and non errors")

    elif filter_errors:
        filter_string = "is_error:1"

    elif filter_non_errors:
        filter_string = "is_error:0"

    else:
        filter_string = ""

    event_iterator = PagingWrapper(
        transfer_client.paginated.task_event_list(
            task_id,
            # TODO: convert to `filter=filter_string` when SDK support is added
            query_params={"filter": filter_string},
        ).items(),
        limit=limit,
    )

    display(
        event_iterator,
        fields=[
            Field("Time", "time"),
            Field("Code", "code"),
            Field("Is Error", "is_error"),
            Field("Details", "details", formatter=SquashedJsonFormatter()),
        ],
        json_converter=iterable_response_to_dict,
    )
