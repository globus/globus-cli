from globus_cli.parsing import group


@group(
    "registered-api",
    lazy_subcommands={
        "show": (".show", "show_command"),
    },
)
def registered_api_command() -> None:
    """Interact with registered APIs in the Globus Flows service."""
