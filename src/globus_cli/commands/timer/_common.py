from __future__ import annotations

import dataclasses
import datetime
import typing as t
from urllib.parse import urlparse

from globus_cli.termio import Field, formatters

# List of datetime formats accepted as input. (`%z` means timezone.)
DATETIME_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
]


class CallbackActionTypeFormatter(formatters.StrFormatter):
    def render(self, value: str) -> str:
        url = urlparse(value)
        if (
            url.netloc.endswith("actions.automate.globus.org")
            and url.path == "/transfer/transfer/run"
        ):
            return "Transfer"
        if (
            url.netloc.startswith("transfer.actions.")
            and url.netloc.endswith(("globus.org", "globuscs.info"))
            and url.path == "/transfer/run"
        ):
            return "Transfer"
        if url.netloc.endswith("flows.automate.globus.org"):
            return "Flow"
        else:
            return value


class TimedeltaFormatter(formatters.FieldFormatter[datetime.timedelta]):
    def parse(self, value: t.Any) -> datetime.timedelta:
        if not isinstance(value, (int, float)):
            raise ValueError("bad timedelta value")
        return datetime.timedelta(seconds=value)

    def render(self, value: datetime.timedelta) -> str:
        return str(value)


class ScheduleFormatter(formatters.FieldFormatter[t.Dict[str, t.Any]]):
    def parse(self, value: t.Any) -> dict[str, t.Any]:
        if not isinstance(value, dict):
            raise ValueError("bad schedule value")
        return value

    def render(self, value: dict[str, t.Any]) -> str:
        if value.get("type") == "once":
            when = value.get("datetime")
            if when:
                timestamp = formatters.Date.render(formatters.Date.parse(when))
                return f"once at {timestamp}"
            else:  # should be unreachable
                return "once"
        elif value.get("type") == "recurring":
            interval = value.get("interval_seconds")
            start = value.get("start")
            if start:
                start = formatters.Date.render(formatters.Date.parse(start))
            end = value.get("end") or {}

            ret = f"every {interval} seconds, starting {start}"
            if end.get("datetime"):
                stop = formatters.Date.render(formatters.Date.parse(end["datetime"]))
                ret += f" and running until {stop}"
            elif end.get("count"):
                ret += f" and running for {end['count']} iterations"
            return ret
        else:  # should be unreachable
            return f"unrecognized schedule type: {value}"


@dataclasses.dataclass
class ParsedActivityInfo:
    code: str
    start_timestamp: str | None
    next_run: str | None


class ActivityFormatter(formatters.FieldFormatter[t.Optional[ParsedActivityInfo]]):
    def parse(self, value: t.Any) -> ParsedActivityInfo | None:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError("bad activity values")

        activity, next_run = value
        if activity is None:
            return None

        if not isinstance(activity, dict):
            raise ValueError("malformed 'activity' field")

        code = activity.get("code")
        if not isinstance(code, str):
            raise ValueError("cannot format activity when 'code' is not a string")

        start_timestamp: str | None = activity.get("start_timestamp")
        if start_timestamp is not None:
            start_timestamp = formatters.Date.format(start_timestamp)

        formatted_next_run: str | None = None
        if next_run is not None:
            formatted_next_run = formatters.Date.format(next_run)

        return ParsedActivityInfo(
            code=code,
            start_timestamp=start_timestamp,
            next_run=formatted_next_run,
        )

    def render(self, value: ParsedActivityInfo | None) -> str:
        if value is None:
            return "This timer is no longer active"

        if value.code == "awaiting_next_run":
            if value.next_run is None:  # unreachable in practice
                return "Awaiting the next run"
            return f"Awaiting the next run, scheduled to occur at {value.next_run}"
        elif value.code == "run_in_progress":
            if value.start_timestamp is None:  # unreachable in practice
                return "Awaiting completion of the latest run"
            return (
                "Awaiting completion of the latest run, "
                f"started at {value.start_timestamp}"
            )
        elif value.code == "retrying":
            if value.start_timestamp is None:  # unreachable in practice
                return "Retrying current run"
            return f"Retrying current run, started at {value.start_timestamp}"
        elif value.code == "paused":
            return "Paused, awaiting user action"
        else:
            return f"<Unrecognized activity.code: {value.code}>"


_COMMON_FIELDS = [
    Field("Timer ID", "job_id"),
    Field("Name", "name"),
    Field("Type", "callback_url", formatter=CallbackActionTypeFormatter()),
    Field("Submitted At", "submitted_at", formatter=formatters.Date),
    Field("Start", "start", formatter=formatters.Date),
    Field("Interval", "interval", formatter=TimedeltaFormatter()),
    Field("Status", "status"),
    Field(
        "Activity",
        "[activity, next_run]",
        formatter=ActivityFormatter(),
    ),
]


TIMER_FORMAT_FIELDS = _COMMON_FIELDS + [
    Field("Last Run", "last_ran_at", formatter=formatters.Date),
    Field("Next Run", "next_run", formatter=formatters.Date),
    Field("Stop After Date", "stop_after.date"),
    Field("Stop After Number of Runs", "stop_after.n_runs"),
    Field("Number of Runs", "n_runs"),
    Field("Number of Timer Errors", "n_errors"),
]

DELETED_TIMER_FORMAT_FIELDS = _COMMON_FIELDS + [
    Field("Stop After Date", "stop_after.date"),
    Field("Stop After Number of Runs", "stop_after.n_runs"),
]
