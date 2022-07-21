import json
import re

import pytest
from globus_sdk import TimerClient
from globus_sdk._testing import RegisteredResponse, load_response, load_response_set

from globus_cli.commands.timer._common import JOB_FORMAT_FIELDS

# NOTE: this is not quite the same as the "normal" job responses from
# create/update—definitely something to consider revisiting on the Timer API.
_job_id = "e304f241-b77a-4e75-89f6-c431ddafe497"
DELETE_RESPONSE = RegisteredResponse(
    metadata={"job_id": _job_id},
    service="timer",
    path=f"/jobs/{_job_id}",
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
                "destination_endpoint": "ddb59af0-6d04-11e5-ba46-22000b92c6ec",
                "encrypt_data": False,
                "fail_on_quota_errors": False,
                "notify_on_failed": True,
                "notify_on_inactive": True,
                "notify_on_succeeded": True,
                "preserve_timestamp": False,
                "recursive_symlinks": "ignore",
                "skip_source_errors": False,
                "source_endpoint": "ddb59aef-6d04-11e5-ba46-22000b92c6ec",
                "submission_id": "548ec2d3-b4fd-11ec-b87f-3912f602f346",
                "verify_checksum": False,
            }
        },
        "callback_url": "https://actions.automate.globus.org/transfer/transfer/run",
        "interval": None,
        "job_id": _job_id,
        "n_tries": 1,
        "name": "example-timer-job",
        "owner": "5276fa05-eedf-46c5-919f-ad2d0160d1a9",
        "refresh_token": None,
        "results": [],
        "start": "2022-04-05T16:27:48",
        "status": "deleted",
        "stop_after": None,
        "stop_after_n": 1,
        "submitted_at": "2022-04-05T16:27:48.805427",
        "update_pending": True,
    },
)


def test_show_job(run_line):
    meta = load_response_set(TimerClient.get_job).metadata
    assert meta
    result = run_line(["globus", "timer", "show", meta["job_id"]])
    assert result.exit_code == 0
    assert meta["job_id"] in result.output
    for field_name, _ in JOB_FORMAT_FIELDS:
        assert field_name in result.output


def test_list_jobs(run_line):
    meta = load_response_set(TimerClient.list_jobs).metadata
    assert meta
    result = run_line(["globus", "timer", "list"])
    assert result.exit_code == 0
    assert all(job_id in result.output for job_id in meta["job_ids"])
    for field_name, _ in JOB_FORMAT_FIELDS:
        assert field_name in result.output


@pytest.mark.parametrize("out_format", ["text", "json"])
def test_delete_job(run_line, out_format):
    meta = load_response(DELETE_RESPONSE).metadata
    add_args = []
    if out_format == "json":
        add_args = ["-F", "json"]
    result = run_line(["globus", "timer", "delete", meta["job_id"]] + add_args)
    assert result.exit_code == 0
    if out_format == "json":
        assert json.loads(result.output) == DELETE_RESPONSE.json
    else:
        pattern = re.compile(
            r"^Job ID:\s+" + re.escape(meta["job_id"]) + "$", flags=re.MULTILINE
        )
        assert pattern.search(result.output) is not None
