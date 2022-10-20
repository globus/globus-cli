from __future__ import annotations

import datetime
import typing as t
from urllib.parse import urlparse

from globus_cli.termio import Field

# List of datetime formats accepted as input. (`%z` means timezone.)
DATETIME_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
]


def _get_stop_date(data: dict[str, t.Any]) -> str | None:
    if not data["stop_after"]:
        return None
    return str(data.get("stop_after", {}).get("date"))


def _get_stop_n_runs(data: dict[str, t.Any]) -> str | None:
    if not data["stop_after"]:
        return None
    return str(data.get("stop_after", {}).get("n_runs"))


def _get_action_type(data: dict[str, t.Any]) -> str:
    url = urlparse(data["callback_url"])
    if (
        url.netloc.endswith("actions.automate.globus.org")
        and url.path == "/transfer/transfer/run"
    ):
        return "Transfer"
    if url.netloc.endswith("flows.automate.globus.org"):
        return "Flow"
    else:
        return str(data["callback_url"])


def _get_interval(data: dict[str, t.Any]) -> str | None:
    if not data["interval"]:
        return None
    return str(datetime.timedelta(seconds=data["interval"]))


JOB_FORMAT_FIELDS = [
    ("Job ID", "job_id"),
    ("Name", "name"),
    ("Type", _get_action_type),
    Field("Submitted At", "submitted_at", formatter=Field.FormatName.Date),
    Field("Start", "start", formatter=Field.FormatName.Date),
    ("Interval", _get_interval),
    Field("Last Run", "last_ran_at", formatter=Field.FormatName.Date),
    Field("Next Run", "next_run", formatter=Field.FormatName.Date),
    ("Stop After Date", _get_stop_date),
    ("Stop After Number of Runs", _get_stop_n_runs),
    ("Number of Runs", lambda data: data["n_runs"]),
    ("Number of Timer Errors", lambda data: data["n_errors"]),
]

DELETED_JOB_FORMAT_FIELDS = [
    ("Job ID", "job_id"),
    ("Name", "name"),
    ("Type", _get_action_type),
    Field("Submitted At", "submitted_at", formatter=Field.FormatName.Date),
    Field("Start", "start", formatter=Field.FormatName.Date),
    ("Interval", _get_interval),
    ("Stop After Date", _get_stop_date),
    ("Stop After Number of Runs", _get_stop_n_runs),
]
