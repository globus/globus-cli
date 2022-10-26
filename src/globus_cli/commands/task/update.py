import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import display

from ._common import task_id_arg


@command(
    "update",
    short_help="Update a task",
    adoc_output=(
        "When text output is requested, the output will be a simple success "
        "message (or an error)."
    ),
    adoc_examples="""Update both label and deadline for a task

[source,bash]
----
$ globus task update TASK_ID --label 'my task updated by me' \
    --deadline '1987-01-22'
----
""",
)
@task_id_arg
@click.option("--label", help="New Label for the task")
@click.option("--deadline", help="New Deadline for the task")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def update_task(*, login_manager: LoginManager, deadline, label, task_id):
    """
    Update label and/or deadline on an active task.

    If a Task has completed, these attributes may no longer be updated.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    transfer_client = login_manager.get_transfer_client()

    task_doc = assemble_generic_doc("task", label=label, deadline=deadline)

    res = transfer_client.update_task(task_id, task_doc)
    display(res, simple_text="Success")
