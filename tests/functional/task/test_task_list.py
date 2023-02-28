import urllib.parse
import uuid

import pytest
import responses
from globus_sdk._testing import get_last_request, load_response_set


def _get_last_request_filter_string():
    last_req = get_last_request()
    parsed_url = urllib.parse.urlparse(last_req.url)
    parsed_params = urllib.parse.parse_qs(parsed_url.query)
    filter_strings = parsed_params["filter"]
    assert len(filter_strings) == 1
    return filter_strings[0]


def _parse_filter_string_to_dict(filter_string):
    ret = {}
    for filter_clause in filter_string.split("/"):
        filter_target, _, filter_value = filter_clause.partition(":")
        ret[filter_target] = filter_value
    return ret


def test_task_list_success(run_line):
    load_response_set("cli.task_list")
    result = run_line("globus task list")
    assert "SUCCEEDED" in result.output
    assert "TRANSFER" in result.output
    # check that empty filters aren't passed through
    filters = dict(
        x.split(":") for x in responses.calls[0].request.params["filter"].split("/")
    )
    assert "completion_time" not in filters
    assert "request_time" not in filters

    # default filter string (compare against other filter tests)
    filter_string = _get_last_request_filter_string()
    assert filter_string == "type:TRANSFER,DELETE"


@pytest.mark.parametrize("filter_type", ("TRANSFER", "DELETE"))
def test_task_list_control_filter_type(run_line, filter_type):
    load_response_set("cli.task_list")
    run_line(["globus", "task", "list", "--filter-type", filter_type])

    filter_string = _get_last_request_filter_string()
    assert filter_string == f"type:{filter_type}"


@pytest.mark.parametrize(
    "filter_status",
    (("ACTIVE",), ("INACTIVE",), ("FAILED", "INACTIVE"), ("ACTIVE", "SUCCEEDED")),
)
def test_task_list_control_filter_status(run_line, filter_status):
    load_response_set("cli.task_list")
    add_args = []
    for filterval in filter_status:
        add_args.append("--filter-status")
        add_args.append(filterval)
    run_line(["globus", "task", "list"] + add_args)

    filter_string = _get_last_request_filter_string()
    parsed_filters = _parse_filter_string_to_dict(filter_string)
    assert parsed_filters["type"] == "TRANSFER,DELETE"
    assert set(parsed_filters) == {"type", "status"}  # set of keys

    statuses_requested = parsed_filters["status"]
    assert set(statuses_requested.split(",")) == set(filter_status)


@pytest.mark.parametrize("inexact", (None, True, False))
@pytest.mark.parametrize(
    "filter_label, filter_not_label",
    (
        (("foo",), ()),
        (("foo", "bar"), ()),
        (("foo",), ("bar",)),
        (("foo",), ("bar", "baz")),
    ),
)
def test_task_list_control_filter_label(
    run_line, inexact, filter_label, filter_not_label
):
    load_response_set("cli.task_list")
    add_args = []
    for label in filter_label:
        add_args.append("--filter-label")
        add_args.append(label)
    for label in filter_not_label:
        add_args.append("--filter-not-label")
        add_args.append(label)
    if inexact is not None:
        if inexact:
            add_args.append("--inexact")
        else:
            add_args.append("--exact")
    inexact_behavior = inexact if inexact is not None else True

    run_line(["globus", "task", "list"] + add_args)

    filter_string = _get_last_request_filter_string()
    parsed_filters = _parse_filter_string_to_dict(filter_string)
    assert parsed_filters["type"] == "TRANSFER,DELETE"
    assert set(parsed_filters) == {"type", "label"}  # set of keys

    labels_requested = parsed_filters["label"].split(",")
    for label in filter_label:
        if inexact_behavior:
            assert f"~{label}" in labels_requested
        else:
            assert f"={label}" in labels_requested
    for label in filter_not_label:
        if inexact_behavior:
            assert f"!~{label}" in labels_requested
        else:
            assert f"!{label}" in labels_requested


# NB: the filter_target is expected to be the exact filter name unless it is "both"
# which means... both :)
@pytest.mark.parametrize("filter_target", ("request_time", "completion_time", "both"))
@pytest.mark.parametrize(
    "before, after",
    (
        ("2020-01-01 00:01:00", None),
        ("2020-01-01 00:01:00", "2019-12-01 12:05:00"),
        (None, "2019-12-01 12:05:00"),
    ),
)
def test_task_list_control_filter_request_and_completion_time(
    run_line, filter_target, before, after
):
    load_response_set("cli.task_list")
    use_request_time = filter_target in ("request_time", "both")
    use_completion_time = filter_target in ("completion_time", "both")
    assert use_request_time or use_completion_time

    add_args = []
    if before:
        if use_request_time:
            add_args.append("--filter-requested-before")
            add_args.append(before)
        if use_completion_time:
            add_args.append("--filter-completed-before")
            add_args.append(before)
    if after:
        if use_request_time:
            add_args.append("--filter-requested-after")
            add_args.append(after)
        if use_completion_time:
            add_args.append("--filter-completed-after")
            add_args.append(after)
    assert add_args

    run_line(["globus", "task", "list"] + add_args)

    filter_string = _get_last_request_filter_string()
    parsed_filters = _parse_filter_string_to_dict(filter_string)
    assert parsed_filters["type"] == "TRANSFER,DELETE"
    if filter_target == "both":
        assert set(parsed_filters) == {"type", "request_time", "completion_time"}
    else:
        assert set(parsed_filters) == {"type", filter_target}

    if use_request_time:
        request_time_filter = parsed_filters["request_time"].split(",")
        assert request_time_filter == [before or "", after or ""]
    if use_completion_time:
        completion_time_filter = parsed_filters["completion_time"].split(",")
        assert completion_time_filter == [before or "", after or ""]


@pytest.mark.parametrize("number_of_ids", (1, 3, 5))
def test_task_list_control_filter_task_id(run_line, number_of_ids):
    load_response_set("cli.task_list")
    add_args = []
    for _ in range(number_of_ids):
        add_args.append("--filter-task-id")
        add_args.append(str(uuid.uuid4()))
    run_line(["globus", "task", "list"] + add_args)

    filter_string = _get_last_request_filter_string()

    parsed_filters = _parse_filter_string_to_dict(filter_string)
    assert parsed_filters["type"] == "TRANSFER,DELETE"
    assert set(parsed_filters) == {"type", "task_id"}  # set of keys

    task_ids = parsed_filters["task_id"].split(",")
    assert len(task_ids) == number_of_ids
    for task_id in task_ids:
        try:
            uuid.UUID(task_id)
        except ValueError:  # clearer failure mode than a "dirty" ValueError
            pytest.fail(f"task_id filter contained non-uuid value: {task_id}")
