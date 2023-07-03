from globus_cli.parsing import group


@group(
    "run",
    lazy_subcommands={
        "update": (".update", "update_command"),
        "delete": (".delete", "delete_command"),
    },
)
def run_command() -> None:
    """Interact with a run in the Globus Flows service"""
