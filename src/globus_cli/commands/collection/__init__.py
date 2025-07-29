from globus_cli.parsing import group


@group(
    "collection",
    lazy_subcommands={
        "create": (".create", "collection_create"),
        "delete": (".delete", "collection_delete"),
        "list": (".list", "collection_list"),
        "role": (".role", "role_command"),
        "show": (".show", "collection_show"),
        "update": (".update", "collection_update"),
    },
)
def collection_command() -> None:
    """Manage your Collections."""
