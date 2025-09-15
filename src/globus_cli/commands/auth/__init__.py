from globus_cli.parsing import group


@group(
    "auth",
    lazy_subcommands={
        "scope": (".scope", "scope_command"),
    },
    # TODO - Make the auth command public once we have >= 5 subcommands
    hidden=True,
)
def auth_command() -> None:
    """Interact with the Globus Auth service."""
