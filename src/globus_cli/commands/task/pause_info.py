import click
import globus_sdk

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import (
    FORMAT_TEXT_RECORD,
    Field,
    field_formatters,
    formatted_print,
)

from ._common import task_id_arg

EXPLICIT_PAUSE_MSG_FIELDS = [
    Field("Source Endpoint", "source_pause_message"),
    Field("Source Shared Endpoint", "source_pause_message_share"),
    Field("Destination Endpoint", "destination_pause_message"),
    Field("Destination Shared Endpoint", "destination_pause_message_share"),
]

PAUSE_RULE_OPERATION_SUBFIELDS = [
    ("write", "pause_task_transfer_write"),
    ("read", "pause_task_transfer_read"),
    ("delete", "pause_task_delete"),
    ("rename", "pause_rename"),
    ("mkdir", "pause_mkdir"),
    ("ls", "pause_ls"),
]

PAUSE_RULE_DISPLAY_FIELDS = [
    Field(
        "Operations",
        lambda rule: "/".join(
            label for label, key in PAUSE_RULE_OPERATION_SUBFIELDS if rule[key]
        ),
    ),
    Field("On Endpoint", "endpoint_display_name"),
    Field(
        "All Users",
        "identity_id",
        formatter=field_formatters.BoolFieldFormatter(true_str="No", false_str="Yes"),
    ),
    Field("Message", "message"),
]


@command(
    "pause-info",
    short_help="Show why an in-progress task is currently paused",
    adoc_output="""
When text output is requested, output is broken apart into explicit pause rules
applied to the specific task (explicit pauses), and "effective pause rules"
which apply to the task by virtue of the endpoint(s) it uses.

Explicit pauses are listed with any of the following fields which apply:

- 'Source Endpoint'
- 'Source Shared Endpoint'
- 'Destination Endpoint'
- 'Destination Shared Endpoint'

which refer to the messages which may be set by these various endpoints.

Effective pause rules are listed with these fields:

- 'Operations'
- 'On Endpoint'
- 'All Users'
- 'Message'
""",
    adoc_examples="""Show why a task is paused, producing JSON output:

[source,bash]
----
$ globus task pause-info TASK_ID --format JSON
----
""",
)
@task_id_arg
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def task_pause_info(*, login_manager: LoginManager, task_id):
    """
    Show messages from activity managers who have explicitly paused the given
    in-progress task and list any active pause rules that apply to it.

    This command displays no information for tasks which are not paused.
    """
    transfer_client = login_manager.get_transfer_client()
    res = transfer_client.task_pause_info(task_id)

    def _custom_text_format(res: globus_sdk.GlobusHTTPResponse) -> None:
        explicit_pauses = [
            field
            for field in EXPLICIT_PAUSE_MSG_FIELDS
            # n.b. some keys are absent for completed tasks
            if field.get_value(res)
        ]
        effective_pause_rules = res["pause_rules"]

        if not explicit_pauses and not effective_pause_rules:
            click.echo(f"Task {task_id} is not paused.")
            click.get_current_context().exit(0)

        if explicit_pauses:
            formatted_print(
                res,
                fields=explicit_pauses,
                text_format=FORMAT_TEXT_RECORD,
                text_preamble="This task has been explicitly paused.\n",
                text_epilog="\n" if effective_pause_rules else None,
            )

        if effective_pause_rules:
            formatted_print(
                effective_pause_rules,
                fields=PAUSE_RULE_DISPLAY_FIELDS,
                text_preamble=(
                    "The following pause rules are effective on this task:\n"
                ),
            )

    formatted_print(res, text_format=_custom_text_format)
