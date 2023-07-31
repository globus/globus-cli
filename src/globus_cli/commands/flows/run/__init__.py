from globus_cli.parsing import group


@group(
    "run",
    lazy_subcommands={
        "show": (".show", "show_command"),
        "list": (".list", "list_command"),
        "update": (".update", "update_command"),
        "delete": (".delete", "delete_command"),
        "resume": (".resume", "resume_command"),
    },
)
def run_command() -> None:
    """Interact with a run in the Globus Flows service"""
