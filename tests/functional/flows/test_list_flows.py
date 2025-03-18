import json
import uuid

from globus_sdk._testing import RegisteredResponse, load_response_set


def test_list_flows(run_line):
    load_response_set("cli.flows_list")

    expected = (
        "Flow ID | Title           | Owner            | Created At          | Updated At         \n"  # noqa: E501
        "------- | --------------- | ---------------- | ------------------- | -------------------\n"  # noqa: E501
        "id-b    | Fairytale Index | shrek@globus.org | 2007-05-18 00:00:00 | 2007-05-18 00:00:00\n"  # noqa: E501
        "id-a    | Swamp Transfer  | shrek@globus.org | 2001-04-01 00:00:00 | 2004-05-19 00:00:00\n"  # noqa: E501
    )

    result = run_line("globus flows list")
    assert result.output == expected


def test_list_flows_json(run_line):
    load_response_set("cli.flows_list")

    result = run_line("globus flows list -F json")
    json.loads(result.output)


def test_list_flows_filter_role(run_line):
    load_response_set("cli.flows_list")

    expected = (
        "Flow ID | Title           | Owner                    | Created At          | Updated At         \n"  # noqa: E501
        "------- | --------------- | ------------------------ | ------------------- | -------------------\n"  # noqa: E501
        "id-bee  | Recover Honey   | barrybbenson@thehive.com | 2007-10-25 00:00:00 | 2007-10-25 00:00:00\n"  # noqa: E501
        "id-b    | Fairytale Index | shrek@globus.org         | 2007-05-18 00:00:00 | 2007-05-18 00:00:00\n"  # noqa: E501
        "id-a    | Swamp Transfer  | shrek@globus.org         | 2001-04-01 00:00:00 | 2004-05-19 00:00:00\n"  # noqa: E501
    )

    result = run_line("globus flows list --filter-role flow_viewer")
    assert result.output == expected


def test_list_flows_invalid_filter_role(run_line):
    load_response_set("cli.flows_list")

    run_line(
        "globus flows list --filter-role this-certainly-isnt-a-valid-role",
        assert_exit_code=2,
    )


def test_list_flows_filter_fulltext(run_line):
    load_response_set("cli.flows_list")

    expected = (
        "Flow ID | Title           | Owner            | Created At          | Updated At         \n"  # noqa: E501
        "------- | --------------- | ---------------- | ------------------- | -------------------\n"  # noqa: E501
        "id-b    | Fairytale Index | shrek@globus.org | 2007-05-18 00:00:00 | 2007-05-18 00:00:00\n"  # noqa: E501
    )

    result = run_line("globus flows list --filter-fulltext Fairytale")
    assert result.output == expected


def test_list_flows_paginated_response(run_line):
    meta = load_response_set("flows_list_paginated").metadata

    result = run_line("globus flows list --limit 1000")
    output_lines = result.output.split("\n")[:-1]  # trim the final newline/empty str
    assert len(output_lines) == meta["total_items"] + 2

    for i, line in enumerate(output_lines[2:]):
        row = line.split(" | ")
        assert row[0] == str(uuid.UUID(int=i))
        # rstrip because this column may be right-padded to align
        #    Hello, World (Example {1})   <-- trailing space
        #    Hello, World (Example {10})  <-- no trailing space
        assert row[1].rstrip() == f"Hello, World (Example {i})"
        assert row[2] == meta["flow_owner"]


def test_list_flows_sorted(run_line):
    meta = load_response_set("flows_list_orderby_title_asc").metadata

    result = run_line(
        ["globus", "flows", "list", "--limit", "100", "--orderby", "title:asc"]
    )
    # trim the final newline/empty str and the header lines
    output_lines = result.output.split("\n")[2:-1]
    assert len(output_lines) == meta["total_items"]

    titles_in_order = []
    for i, line in enumerate(output_lines):
        row = line.split(" | ")
        assert row[0] == str(uuid.UUID(int=i))
        titles_in_order.append(row[1].strip())
        assert row[2] == meta["flow_owner"]

    assert titles_in_order == sorted(titles_in_order)


def test_list_flows_empty_list(run_line):
    RegisteredResponse(service="flows", path="/flows", json={"flows": []}).add()

    expected = (
        "Flow ID | Title | Owner | Created At | Updated At\n"
        "------- | ----- | ----- | ---------- | ----------\n"
    )

    result = run_line("globus flows list")
    assert result.output == expected
