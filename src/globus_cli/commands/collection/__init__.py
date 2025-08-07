from globus_cli.parsing import group


@group(
    "collection",
    lazy_subcommands={
        "create": (".create", "collection_create"),
        "delete": (".delete", "collection_delete"),
        "list": (".list", "collection_list"),
        "show": (".show", "collection_show"),
        "update": (".update", "collection_update"),
        "role": (".role", "role_command"),
    },
)
def collection_command() -> None:
    """Manage your Collections."""
