from __future__ import annotations

import sys
import typing as t
from datetime import datetime
from functools import wraps

import click
import globus_sdk

from globus_cli.commands.timer._common import DATETIME_FORMATS, ScheduleFormatter
from globus_cli.parsing import TimedeltaType, mutex_option_group
from globus_cli.termio import Field, formatters

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

R = t.TypeVar("R")


CREATE_FORMAT_FIELDS = [
    Field("Timer ID", "job_id"),
    Field("Name", "name"),
    Field("Type", "timer_type"),
    Field("Submitted At", "submitted_at", formatter=formatters.Date),
    Field("Status", "status"),
    Field("Last Run", "last_ran_at", formatter=formatters.Date),
    Field("Next Run", "next_run", formatter=formatters.Date),
    Field("Schedule", "schedule", formatter=ScheduleFormatter()),
    Field("Number of Runs", "number_of_runs"),
    Field("Number of Timer Errors", "number_of_errors"),
]


TimerSchedule: TypeAlias = t.Union[
    globus_sdk.RecurringTimerSchedule,
    globus_sdk.OnceTimerSchedule,
]


def timer_schedule_options(f: t.Callable[..., R]) -> t.Callable[..., R]:
    """
    A decorator which register "schedule" related timer options on a command.

    The options registered are:
        --start
        --interval
        --stop-after-date
        --stop-after-runs

    While these are registered and enforced in specific ways, the handler function
    receives a single `schedule: TimerSchedule` loaded argument.

    Usage:
    >>> @timer_schedule_options
    >>> def my_great_timer_command(schedule: TimerSchedule):
    >>>     ...
    """

    @click.option(
        "--start",
        type=click.DateTime(formats=DATETIME_FORMATS),
        help="Start time for the timer. Defaults to current time.",
    )
    @click.option(
        "--interval",
        type=TimedeltaType(),
        help=("""\
            Interval at which the timer should run. Expressed in weeks, days, hours,
            minutes, and seconds. Use 'w', 'd', 'h', 'm', and 's' as suffixes to
            specify. e.g. '1h30m', '500s', '10d'
            """),
    )
    @click.option(
        "--stop-after-date",
        type=click.DateTime(formats=DATETIME_FORMATS),
        help="Stop running the transfer after this date.",
    )
    @click.option(
        "--stop-after-runs",
        type=click.IntRange(min=1),
        help="Stop running the transfer after this number of runs have happened.",
    )
    @mutex_option_group("--stop-after-date", "--stop-after-runs")
    @wraps(f)
    def wrapper(
        *args: t.Any,
        start: datetime | None,
        interval: int | None,
        stop_after_date: datetime | None,
        stop_after_runs: int | None,
        **kwargs: t.Any,
    ) -> R:
        schedule = _create_schedule(start, interval, stop_after_date, stop_after_runs)

        return f(*args, schedule=schedule, **kwargs)

    return wrapper


def _create_schedule(
    start: datetime | None,
    interval: int | None,
    stop_after_date: datetime | None,
    stop_after_runs: int | None,
) -> TimerSchedule:
    """
    Create a composite TimerSchedule object from user input.

    :raises click.UsageError: if the input is invalid/incoherent in some way.
    :returns: Either a RecurringTimerSchedule or a OnceTimerSchedule
    """
    start_ = _to_local_tz(start)
    if stop_after_runs == 1:
        if interval is not None:
            raise click.UsageError("`--interval` is invalid with `--stop-after-runs=1`")
        return globus_sdk.OnceTimerSchedule(datetime=start_)
    else:
        if interval is None:
            raise click.UsageError(
                "`--interval` is required unless `--stop-after-runs=1`"
            )

        end: dict[str, t.Any] | globus_sdk.MissingType = globus_sdk.MISSING
        # reminder: these two cases are mutex
        if stop_after_runs is not None:
            end = {
                "condition": "iterations",
                "count": stop_after_runs,
            }
        elif stop_after_date is not None:
            end = {
                "condition": "time",
                "datetime": _to_local_tz(stop_after_date),
            }

        return globus_sdk.RecurringTimerSchedule(
            interval_seconds=interval, end=end, start=start_
        )


def _to_local_tz(start: datetime | None) -> datetime | globus_sdk.MissingType:
    if start is None:
        return globus_sdk.MISSING

    # set the timezone to local system time if the timezone input is not aware
    start_with_tz = start.astimezone() if start.tzinfo is None else start
    return start_with_tz
