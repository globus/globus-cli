from globus_cli.parsing import group


@group(
    "collection",
    lazy_subcommands={
        "delete": (".delete", "collection_delete"),
        "list": (".list", "collection_list"),
        "show": (".show", "collection_show"),
        "update": (".update", "collection_update"),
    },
)
def collection_command() -> None:
    """Manage your Collections"""
