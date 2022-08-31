from globus_cli.parsing import group


@group(
    "task",
    lazy_subcommands={
        "cancel": (".cancel", "cancel_task"),
        "event-list": (".event_list", "task_event_list"),
        "generate-submission-id": (".generate_submission_id", "generate_submission_id"),
        "list": (".list", "task_list"),
        "pause-info": (".pause_info", "task_pause_info"),
        "show": (".show", "show_task"),
        "update": (".update", "update_task"),
        "wait": (".wait", "task_wait"),
    },
)
def task_command() -> None:
    """Manage asynchronous tasks"""
