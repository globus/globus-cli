from globus_cli.parsing import group


@group(
    "task",
    lazy_subcommands={
        "list": (".list", "list_command"),
        "show": (".show", "show_command"),
    },
)
def task_command() -> None:
    """View Task documents"""
