from __future__ import annotations

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
        if url.netloc.endswith("flows.automate.globus.org"):
            return "Flow"
        else:
            return value


class TimedeltaFormatter(formatters.FieldFormatter[datetime.timedelta]):
    def parse(self, value: t.Any) -> datetime.timedelta:
        if not isinstance(value, int):
            raise ValueError("bad timedelta value")
        return datetime.timedelta(seconds=value)

    def render(self, value: datetime.timedelta) -> str:
        return str(value)


_COMMON_FIELDS = [
    Field("Job ID", "job_id"),
    Field("Name", "name"),
    Field("Type", "callback_url", formatter=CallbackActionTypeFormatter()),
    Field("Submitted At", "submitted_at", formatter=formatters.Date),
    Field("Start", "start", formatter=formatters.Date),
    Field("Interval", "interval", formatter=TimedeltaFormatter()),
]


JOB_FORMAT_FIELDS = _COMMON_FIELDS + [
    Field("Status", "status"),
    Field("Last Run", "last_ran_at", formatter=formatters.Date),
    Field("Next Run", "next_run", formatter=formatters.Date),
    Field("Stop After Date", "stop_after.date"),
    Field("Stop After Number of Runs", "stop_after.n_runs"),
    Field("Number of Runs", "n_runs"),
    Field("Number of Timer Errors", "n_errors"),
]

DELETED_JOB_FORMAT_FIELDS = _COMMON_FIELDS + [
    Field("Stop After Date", "stop_after.date"),
    Field("Stop After Number of Runs", "stop_after.n_runs"),
]
