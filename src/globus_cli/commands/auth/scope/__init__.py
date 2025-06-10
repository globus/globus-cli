from globus_cli.parsing import group


@group(
    "scope",
    lazy_subcommands={
        "show": (".show", "show_command"),
    },
)
def scope_command() -> None:
    """Interact with a scope in the Globus Auth service."""
