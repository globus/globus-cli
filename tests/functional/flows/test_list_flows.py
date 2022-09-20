import json

from globus_sdk._testing import load_response_set


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
