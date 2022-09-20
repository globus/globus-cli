from __future__ import annotations

import datetime
from typing import Any
from urllib.parse import urlparse

from globus_cli.commands._common import isoformat_to_local

# List of datetime formats accepted as input. (`%z` means timezone.)
DATETIME_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
]


def _get_stop_date(data: dict[str, Any]) -> str | None:
    if not data["stop_after"]:
        return None
    return str(data.get("stop_after", {}).get("date"))


def _get_stop_n_runs(data: dict[str, Any]) -> str | None:
    if not data["stop_after"]:
        return None
    return str(data.get("stop_after", {}).get("n_runs"))


def _get_action_type(data: dict[str, Any]) -> str:
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


def _get_interval(data: dict[str, Any]) -> str | None:
    if not data["interval"]:
        return None
    return str(datetime.timedelta(seconds=data["interval"]))


JOB_FORMAT_FIELDS = [
    ("Job ID", "job_id"),
    ("Name", "name"),
    ("Type", _get_action_type),
    ("Submitted At", lambda data: isoformat_to_local(data["submitted_at"])),
    ("Start", lambda data: isoformat_to_local(data["start"])),
    ("Interval", _get_interval),
    ("Last Run", lambda data: isoformat_to_local(data["last_ran_at"])),
    ("Next Run", lambda data: isoformat_to_local(data["next_run"])),
    ("Stop After Date", _get_stop_date),
    ("Stop After Number of Runs", _get_stop_n_runs),
    ("Number of Runs", lambda data: data["n_runs"]),
    ("Number of Timer Errors", lambda data: data["n_errors"]),
]

DELETED_JOB_FORMAT_FIELDS = [
    ("Job ID", "job_id"),
    ("Name", "name"),
    ("Type", _get_action_type),
    ("Submitted At", lambda data: isoformat_to_local(data["submitted_at"])),
    ("Start", lambda data: isoformat_to_local(data["start"])),
    ("Interval", _get_interval),
    ("Stop After Date", _get_stop_date),
    ("Stop After Number of Runs", _get_stop_n_runs),
]
