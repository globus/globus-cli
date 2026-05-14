import json
import urllib.parse
import uuid

from globus_sdk.testing import RegisteredResponse, get_last_request, load_response_set


def test_list_registered_apis(run_line):
    load_response_set("cli.registered_apis_list")

    expected = (
        "Registered API ID                    | Name             | Created At          | Updated At         \n"  # noqa: E501
        "-------------------------------------+------------------+---------------------+--------------------\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000001 | registered-api-1 | 2024-01-01 18:00:00 | 2024-01-01 19:00:00\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000000 | registered-api-0 | 2023-12-31 18:00:00 | 2023-12-31 18:00:00\n"  # noqa: E501
    )

    result = run_line("globus flows registered-api list")
    assert result.output == expected

    # confirm that none of the filtering parameters were sent to the API
    # and that the default orderby was sent
    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_params = urllib.parse.parse_qs(parsed_url.query)
    assert "filter_roles" not in parsed_params
    assert "orderby" in parsed_params
    assert parsed_params["orderby"] == ["created_timestamp DESC"]


def test_list_registered_apis_json(run_line):
    load_response_set("cli.registered_apis_list")

    result = run_line("globus flows registered-api list -F json")
    json.loads(result.output)


def test_list_registered_apis_filter_role_single(run_line):
    load_response_set("cli.registered_apis_list_filtered")

    expected = (
        "Registered API ID                    | Name             | Created At          | Updated At         \n"  # noqa: E501
        "-------------------------------------+------------------+---------------------+--------------------\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000002 | registered-api-2 | 2024-01-02 18:00:00 | 2024-01-02 20:00:00\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000001 | registered-api-1 | 2024-01-01 18:00:00 | 2024-01-01 19:00:00\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000000 | registered-api-0 | 2023-12-31 18:00:00 | 2023-12-31 18:00:00\n"  # noqa: E501
    )

    result = run_line("globus flows registered-api list --filter-role owner")
    assert result.output == expected

    # verify the filter_roles parameter was sent
    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_params = urllib.parse.parse_qs(parsed_url.query)
    assert "filter_roles" in parsed_params
    assert parsed_params["filter_roles"] == ["owner"]


def test_list_registered_apis_filter_role_multiple(run_line):
    load_response_set("cli.registered_apis_list_filtered")

    expected = (
        "Registered API ID                    | Name             | Created At          | Updated At         \n"  # noqa: E501
        "-------------------------------------+------------------+---------------------+--------------------\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000002 | registered-api-2 | 2024-01-02 18:00:00 | 2024-01-02 20:00:00\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000001 | registered-api-1 | 2024-01-01 18:00:00 | 2024-01-01 19:00:00\n"  # noqa: E501
        "00000000-0000-0000-0000-000000000000 | registered-api-0 | 2023-12-31 18:00:00 | 2023-12-31 18:00:00\n"  # noqa: E501
    )

    result = run_line(
        [
            "globus",
            "flows",
            "registered-api",
            "list",
            "--filter-role",
            "owner",
            "--filter-role",
            "administrator",
        ]
    )
    assert result.output == expected

    # verify both filter_roles parameters were sent as comma-separated values
    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_params = urllib.parse.parse_qs(parsed_url.query)
    assert "filter_roles" in parsed_params
    assert parsed_params["filter_roles"] == ["owner,administrator"]


def test_list_registered_apis_invalid_filter_role(run_line):
    load_response_set("cli.registered_apis_list")

    run_line(
        [
            "globus",
            "flows",
            "registered-api",
            "list",
            "--filter-role",
            "this-certainly-isnt-a-valid-role",
        ],
        assert_exit_code=2,
    )


def test_list_registered_apis_paginated_response(run_line):
    meta = load_response_set("registered_apis_list_paginated").metadata
    total_items = meta["total_items"]

    result = run_line("globus flows registered-api list --limit 1000")
    output_lines = result.output.split("\n")[:-1]  # trim the final newline/empty str
    # 2 header lines + total_items data lines
    assert len(output_lines) == total_items + 2

    for i, line in enumerate(output_lines[2:]):
        row = line.split(" | ")
        assert row[0] == str(uuid.UUID(int=i))
        # rstrip because this column may be right-padded to align
        assert row[1].rstrip() == f"registered-api-{i}"


def test_list_registered_apis_sorted(run_line):
    meta = load_response_set("registered_apis_list_orderby_name_asc").metadata
    total_items = meta["total_items"]

    result = run_line(
        [
            "globus",
            "flows",
            "registered-api",
            "list",
            "--limit",
            "100",
            "--orderby",
            "name:asc",
        ]
    )
    # trim the final newline/empty str and the header lines
    output_lines = result.output.split("\n")[2:-1]
    assert len(output_lines) == total_items

    names_in_order = []
    for i, line in enumerate(output_lines):
        row = line.split(" | ")
        assert row[0] == str(uuid.UUID(int=i))
        names_in_order.append(row[1].strip())

    assert names_in_order == sorted(names_in_order)


def test_list_registered_apis_empty_list(run_line):
    RegisteredResponse(
        service="flows",
        path="/registered_apis",
        json={"registered_apis": [], "has_next_page": False, "marker": None},
    ).add()

    expected = (
        "Registered API ID | Name | Created At | Updated At\n"
        "------------------+------+------------+-----------\n"
    )

    result = run_line("globus flows registered-api list")
    assert result.output == expected
