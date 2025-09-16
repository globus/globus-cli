import datetime

import pytest

from globus_cli.commands.timer._common import (
    ActivityFormatter,
    CallbackActionTypeFormatter,
    ScheduleFormatter,
)
from globus_cli.termio.formatters import FormattingFailedWarning


@pytest.mark.parametrize(
    "value, expected",
    (
        ("https://actions.automate.globus.org/transfer/transfer/run", "Transfer"),
        ("https://transfer.actions.integration.globuscs.info/transfer/run", "Transfer"),
        ("https://flows.automate.globus.org", "Flow"),
        ("bogus", "bogus"),
    ),
)
def test_action_formatter(value, expected):
    assert CallbackActionTypeFormatter().render(value) == expected


start_string = "2023-12-19T21:00:00+03:00"
end_string = "2024-01-01T15:16:17-14:00"
start_rendered = (
    datetime.datetime.fromisoformat(start_string)
    .astimezone()
    .strftime("%Y-%m-%d %H:%M:%S")
)
end_rendered = (
    datetime.datetime.fromisoformat(end_string)
    .astimezone()
    .strftime("%Y-%m-%d %H:%M:%S")
)


@pytest.mark.parametrize(
    "value, expected",
    (
        pytest.param(
            {
                "end": {"count": 3},
                "interval_seconds": 86400,
                "start": start_string,
                "type": "recurring",
            },
            (
                f"every 86400 seconds, starting {start_rendered} and running for "
                "3 iterations"
            ),
            id="start-end-count",
        ),
        pytest.param(
            {
                "end": {"datetime": end_string},
                "interval_seconds": 86400,
                "start": start_string,
                "type": "recurring",
            },
            (
                f"every 86400 seconds, starting {start_rendered} and running "
                f"until {end_rendered}"
            ),
            id="start-end-datetime",
        ),
        pytest.param(
            {
                "datetime": start_string,
                "type": "once",
            },
            f"once at {start_rendered}",
            id="start-once",
        ),
    ),
)
def test_schedule_formatter(value, expected):
    assert ScheduleFormatter().render(value) == expected


start_string = "1988-12-19T21:00:00+00:00"
start_rendered = (
    datetime.datetime.fromisoformat(start_string)
    .astimezone()
    .strftime("%Y-%m-%d %H:%M:%S")
)
next_run_string = "1992-06-07T10:18:00+00:00"
next_run_rendered = (
    datetime.datetime.fromisoformat(next_run_string)
    .astimezone()
    .strftime("%Y-%m-%d %H:%M:%S")
)


@pytest.mark.parametrize(
    "value, expected",
    (
        pytest.param([None, None], "This timer is no longer active", id="nulls"),
        pytest.param(
            [{"code": "awaiting_next_run"}, next_run_string],
            f"Awaiting the next run, scheduled to occur at {next_run_rendered}",
            id="awaiting-next",
        ),
        pytest.param(
            [{"code": "awaiting_next_run"}, None],
            "Awaiting the next run",
            id="awaiting-no-next-run-time",
        ),
        pytest.param(
            [{"code": "run_in_progress", "start_timestamp": start_string}, None],
            f"Awaiting completion of the latest run, started at {start_rendered}",
            id="in-progress",
        ),
        pytest.param(
            [{"code": "run_in_progress"}, None],
            "Awaiting completion of the latest run",
            id="in-progress-no-start-time",
        ),
        pytest.param(
            [{"code": "retrying", "start_timestamp": start_string}, None],
            f"Retrying current run, started at {start_rendered}",
            id="retrying",
        ),
        pytest.param(
            [{"code": "retrying"}, None],
            "Retrying current run",
            id="retrying-no-start-time",
        ),
        pytest.param(
            [{"code": "paused"}, None], "Paused, awaiting user action", id="paused"
        ),
        pytest.param(
            [{"code": "UNKNOWN_CODE"}, None],
            "<Unrecognized activity.code: UNKNOWN_CODE>",
            id="unknown",
        ),
    ),
)
def test_activity_formatter(value, expected):
    assert ActivityFormatter().format(value) == expected


@pytest.mark.parametrize(
    "value, expect_error",
    (
        pytest.param({}, "bad activity values", id="non-list"),
        pytest.param([], "bad activity values", id="empty-list"),
        pytest.param([None], "bad activity values", id="singleton-list"),
        pytest.param([None, None, None], "bad activity values", id="list-too-long"),
        pytest.param(
            ["paused", None], "malformed 'activity' field", id="non-dict-activity"
        ),
        pytest.param(
            [{"code": 0}, None],
            "cannot format activity when 'code' is not a string",
            id="non-string-code",
        ),
    ),
)
def test_activity_formatter_rejects_unexpected_values(value, expect_error):
    with pytest.raises(ValueError, match=expect_error):
        ActivityFormatter().parse(value)


@pytest.mark.parametrize(
    "value, expect_result",
    (
        # these next tests check the behavior of the inner date formatter
        pytest.param(
            [{"code": "awaiting_next_run"}, 0],
            "Awaiting the next run, scheduled to occur at 0",
            id="non-string-next-run",
        ),
        pytest.param(
            [{"code": "awaiting_next_run"}, "not okay"],
            "Awaiting the next run, scheduled to occur at not okay",
            id="non-iso-next-run",
        ),
        pytest.param(
            [{"code": "retrying", "start_timestamp": 0}, None],
            "Retrying current run, started at 0",
            id="non-string-start-timestamp",
        ),
        pytest.param(
            [{"code": "retrying", "start_timestamp": "not okay"}, None],
            "Retrying current run, started at not okay",
            id="non-iso-start-timestamp",
        ),
    ),
)
def test_activity_formatter_handling_of_invalid_inner_dates(value, expect_result):
    # when one of the date fields is present but not a valid date, we get handling
    # from inner date formatting, so we emit errors but still "format"
    with pytest.warns(FormattingFailedWarning, match="Formatting failed"):
        assert ActivityFormatter().format(value) == expect_result
