from globus_cli.parsing import group


@group(
    "bookmark",
    lazy_subcommands={
        "create": (".create", "bookmark_create"),
        "delete": (".delete", "bookmark_delete"),
        "list": (".list", "bookmark_list"),
        "rename": (".rename", "bookmark_rename"),
        "show": (".show", "bookmark_show"),
    },
)
def bookmark_command() -> None:
    """Manage endpoint bookmarks"""
