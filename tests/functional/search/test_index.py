from globus_sdk._testing import load_response, load_response_set


def test_index_list(run_line):
    meta = load_response_set("cli.search").metadata
    list_data = meta["index_list_data"]

    result = run_line(["globus", "search", "index", "list"])

    found = set()
    for index_id, attrs in list_data.items():
        for line in result.output.split("\n"):
            if index_id in line:
                found.add(index_id)
                for v in attrs.values():
                    assert v in line
    assert len(found) == len(list_data)


def test_index_show(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    run_line(
        ["globus", "search", "index", "show", index_id],
        search_stdout=("Index ID", index_id),
    )


def test_index_create(run_line):
    meta = load_response("search.create_index").metadata
    index_id = meta["index_id"]

    run_line(
        [
            "globus",
            "search",
            "index",
            "create",
            "example_cookery",
            "Example index of Cookery",
        ],
        search_stdout=("Index ID", index_id),
    )


def test_index_delete(run_line):
    meta = load_response("search.delete_index").metadata
    index_id = meta["index_id"]

    run_line(
        f"globus search index delete {index_id}",
        search_stdout=f"Index {index_id} is now marked for deletion.",
    )


def test_index_delete_rejects_empty_str(run_line):
    result = run_line(["globus", "search", "index", "delete", ""], assert_exit_code=2)
    assert "Invalid value for 'INDEX_ID'" in result.stderr
