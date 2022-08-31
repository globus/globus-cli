from globus_cli.parsing import group


@group(
    "session",
    lazy_subcommands={
        "consent": (".consent", "session_consent"),
        "show": (".show", "session_show"),
        "update": (".update", "session_update"),
    },
)
def session_command() -> None:
    """Manage your CLI auth session"""
