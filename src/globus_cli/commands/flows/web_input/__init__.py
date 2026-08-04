from globus_cli.parsing import group


@group(
    "web-input",
    lazy_subcommands={
        "show": (".show", "show_command"),
        "list": (".list", "list_command"),
        "respond": (".respond", "respond_command"),
    },
)
def web_input_command() -> None:
    """Interact with web inputs in the Globus Flows service."""
