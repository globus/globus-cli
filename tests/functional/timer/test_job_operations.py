import json
import re

import globus_sdk
import pytest
from globus_sdk.testing import RegisteredResponse, load_response, load_response_set

from globus_cli.commands.timer._common import TIMER_FORMAT_FIELDS

# NOTE: this is not quite the same as the "normal" timer responses from
# create/update—definitely something to consider revisiting on the Timer API.
_timer_id = "e304f241-b77a-4e75-89f6-c431ddafe497"
DELETE_RESPONSE = RegisteredResponse(
    metadata={"timer_id": _timer_id},
    service="timer",
    path=f"/jobs/{_timer_id}",
    method="DELETE",
    json={
        "callback_body": {
            "body": {
                "DATA": [
                    {
                        "DATA_TYPE": "transfer_item",
                        "checksum_algorithm": None,
                        "destination_path": "/~/file1.txt",
                        "external_checksum": None,
                        "recursive": False,
                        "source_path": "/share/godata/file1.txt",
                    }
                ],
                "DATA_TYPE": "transfer",
                "delete_destination_extra": False,
                "destination_endpoint": "313ce13e-b597-5858-ae13-29e46fea26e6",
                "encrypt_data": False,
                "fail_on_quota_errors": False,
                "notify_on_failed": True,
                "notify_on_inactive": True,
                "notify_on_succeeded": True,
                "preserve_timestamp": False,
                "recursive_symlinks": "ignore",
                "skip_source_errors": False,
                "source_endpoint": "aa752cea-8222-5bc8-acd9-555b090c0ccb",
                "submission_id": "548ec2d3-b4fd-11ec-b87f-3912f602f346",
                "verify_checksum": False,
            }
        },
        "callback_url": "https://actions.automate.globus.org/transfer/transfer/run",
        "interval": None,
        "job_id": _timer_id,
        "n_tries": 1,
        "name": "example-timer",
        "owner": "5276fa05-eedf-46c5-919f-ad2d0160d1a9",
        "refresh_token": None,
        "results": [],
        "start": "2022-04-05T16:27:48",
        "status": "deleted",
        "stop_after": None,
        "stop_after_n": 1,
        "submitted_at": "2022-04-05T16:27:48.805427",
        "update_pending": True,
        "activity": None,
    },
)


def test_show_timer(run_line):
    meta = load_response_set(globus_sdk.TimersClient.get_job).metadata
    assert meta
    result = run_line(["globus", "timer", "show", meta["job_id"]])
    assert result.exit_code == 0
    assert meta["job_id"] in result.output
    for field in TIMER_FORMAT_FIELDS:
        assert field.name in result.output


def test_list_timers(run_line):
    meta = load_response_set(globus_sdk.TimersClient.list_jobs).metadata
    assert meta
    result = run_line(["globus", "timer", "list"])
    assert result.exit_code == 0
    assert all(timer_id in result.output for timer_id in meta["job_ids"])
    for field in TIMER_FORMAT_FIELDS:
        assert field.name in result.output


@pytest.mark.parametrize("out_format", ["text", "json"])
def test_delete_timer(run_line, out_format):
    meta = load_response(DELETE_RESPONSE).metadata
    add_args = []
    if out_format == "json":
        add_args = ["-F", "json"]
    result = run_line(["globus", "timer", "delete", meta["timer_id"]] + add_args)
    assert result.exit_code == 0
    if out_format == "json":
        assert json.loads(result.output) == DELETE_RESPONSE.json
    else:
        pattern = re.compile(
            r"^Timer ID:\s+" + re.escape(meta["timer_id"]) + "$", flags=re.MULTILINE
        )
        assert pattern.search(result.output) is not None


def test_pause_timer(run_line):
    meta = load_response_set(globus_sdk.TimersClient.pause_job).metadata
    add_args = []
    run_line(
        ["globus", "timer", "pause", meta["job_id"]] + add_args,
        search_stdout=f"Successfully paused job {meta['job_id']}.",
    )
