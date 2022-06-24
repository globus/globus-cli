from globus_sdk._testing import load_response_set


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

    result, matcher = run_line(
        ["globus", "search", "index", "show", index_id], matcher=True
    )
    matcher.check(r"^Index ID:\s+([\w-]+)$", groups=[index_id])


def test_index_create(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    result, matcher = run_line(
        [
            "globus",
            "search",
            "index",
            "create",
            "example_cookery",
            "Example index of Cookery",
        ],
        matcher=True,
    )
    matcher.check(r"^Index ID:\s+([\w-]+)$", groups=[index_id])


def test_index_delete(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    result = run_line(f"globus search index delete {index_id}")
    assert f"Index {index_id} is now marked for deletion." in result.output
