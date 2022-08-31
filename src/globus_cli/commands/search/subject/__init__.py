from globus_cli.parsing import group


@group(
    "subject",
    short_help="Manage data by subject",
    lazy_subcommands={
        "delete": (".delete", "delete_command"),
        "show": (".show", "show_command"),
    },
)
def subject_command() -> None:
    """View and manage individual documents in an index by subject"""
