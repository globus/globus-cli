from globus_cli.parsing import group


@group(
    "search",
    lazy_subcommands={
        "delete-by-query": (".delete_by_query", "delete_by_query_command"),
        "index": (".index", "index_command"),
        "ingest": (".ingest", "ingest_command"),
        "query": (".query", "query_command"),
        "subject": (".subject", "subject_command"),
        "task": (".task", "task_command"),
    },
)
def search_command():
    """Use Globus Search to store and query for data"""
