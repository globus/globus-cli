import datetime
import json
import uuid

import globus_sdk
import pytest
from globus_sdk._testing import RegisteredResponse, get_last_request, load_response


@pytest.fixture
def non_ha_mapped_collection():
    mapped_collection_id = "1405823f-0597-4a16-b296-46d4f0ae4b15"
    client_id = "cf37806c-572c-47ff-88e2-511c646ef1a4"
    load_response(
        RegisteredResponse(
            service="transfer",
            path=f"/endpoint/{mapped_collection_id}",
            method="GET",
            json={
                "DATA": [
                    {"DATA_TYPE": "server", "hostname": "abc.xyz.data.globus.org"}
                ],
                "DATA_TYPE": "endpoint",
                "activated": False,
                "canonical_name": f"{client_id}#{mapped_collection_id}",
                "contact_email": None,
                "contact_info": None,
                "default_directory": None,
                "description": "example gcsv5 mapped collection",
                "department": None,
                "display_name": "Happy Fun Mapped Collection Name",
                "entity_type": "GCSv5_mapped_collection",
                "force_encryption": False,
                "gcs_version": "5.4.10",
                "host_endpoint_id": None,
                "id": mapped_collection_id,
                "is_globus_connect": False,
                "info_link": None,
                "keywords": None,
                "local_user_info_available": False,
                "non_functional": False,
                "organization": "My Org",
                "owner_id": client_id,
                "owner_string": f"{client_id}@clients.auth.globus.org",
                "public": False,
                "shareable": False,
                "subscription_id": None,
                "high_assurance": False,
            },
        )
    )
    load_response(
        RegisteredResponse(
            path=f"/endpoint/{mapped_collection_id}/autoactivate",
            service="transfer",
            method="POST",
            json={"code": "Activated.BogusCode"},
        )
    )
    return mapped_collection_id


@pytest.fixture
def ep_for_timer():
    load_response(globus_sdk.TimerClient.create_job)
    load_response(globus_sdk.TransferClient.get_submission_id)
    ep_meta = load_response(globus_sdk.TransferClient.get_endpoint).metadata
    ep_id = ep_meta["endpoint_id"]
    load_response(
        RegisteredResponse(
            path=f"/endpoint/{ep_id}/autoactivate",
            service="transfer",
            method="POST",
            json={"code": "Activated.BogusCode"},
        )
    )
    return ep_id


@pytest.mark.parametrize(
    "extra_args",
    [
        ["--interval", "600s"],
        ["--stop-after-runs", "1"],
    ],
)
def test_create_job_simple(run_line, ep_for_timer, extra_args):
    run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--name",
            "test-transfer-command",
            f"{ep_for_timer}:/file1",
            f"{ep_for_timer}:/file2",
        ]
        + extra_args
    )

    sent_data = json.loads(get_last_request().body)
    transfer_body = sent_data["callback_body"]["body"]
    assert transfer_body["DATA_TYPE"] == "transfer"
    assert isinstance(transfer_body["DATA"], list)
    assert len(transfer_body["DATA"]) == 1
    assert transfer_body["DATA"][0]["DATA_TYPE"] == "transfer_item"
    assert transfer_body["DATA"][0]["source_path"] == "/file1"
    assert transfer_body["DATA"][0]["destination_path"] == "/file2"


def test_create_job_batch_data(run_line, ep_for_timer):
    batch_input = "abc /def\n/xyz p/q/r\n"

    run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            ep_for_timer,
            ep_for_timer,
            "--interval",
            "1800s",
            "--batch",
            "-",
        ],
        stdin=batch_input,
    )

    sent_data = json.loads(get_last_request().body)
    transfer_body = sent_data["callback_body"]["body"]
    assert transfer_body["DATA_TYPE"] == "transfer"
    assert isinstance(transfer_body["DATA"], list)
    assert len(transfer_body["DATA"]) == 2
    assert transfer_body["DATA"][0]["DATA_TYPE"] == "transfer_item"
    assert transfer_body["DATA"][1]["DATA_TYPE"] == "transfer_item"
    assert transfer_body["DATA"][0]["source_path"] == "abc"
    assert transfer_body["DATA"][0]["destination_path"] == "/def"
    assert transfer_body["DATA"][1]["source_path"] == "/xyz"
    assert transfer_body["DATA"][1]["destination_path"] == "p/q/r"


def test_recursive_and_batch_exclusive(run_line):
    ep_id = str(uuid.UUID(int=1))

    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            ep_id,
            ep_id,
            "--interval",
            "1800s",
            "--recursive",
            "--batch",
            "-",
        ],
        assert_exit_code=2,
    )
    assert "You cannot use --recursive in addition to --batch" in result.stderr


def test_create_job_requires_some_pathargs(run_line):
    ep_id = str(uuid.UUID(int=1))

    result = run_line(
        ["globus", "timer", "create", "transfer", ep_id, ep_id, "--interval", "1800s"],
        assert_exit_code=2,
    )
    assert (
        "transfer requires either SOURCE_PATH and DEST_PATH or --batch" in result.stderr
    )


def test_interval_usually_required(run_line):
    ep_id = str(uuid.UUID(int=1))

    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{ep_id}:/foo/",
            f"{ep_id}:/bar/",
        ],
        assert_exit_code=2,
    )
    assert (
        "'--interval' is required unless `--stop-after-runs=1` is used" in result.stderr
    )


def test_interval_not_required_if_stop_after_is_one(run_line, ep_for_timer):
    run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{ep_for_timer}:/foo/",
            f"{ep_for_timer}:/bar/",
            "--stop-after-runs",
            "1",
        ],
    )
    sent_data = json.loads(get_last_request().body)
    assert sent_data["stop_after_n"] == 1


def test_start_time_allows_timezone(run_line, ep_for_timer):
    # explicit timezone is preserved in the formatted data sent to the service
    run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{ep_for_timer}:/foo/",
            f"{ep_for_timer}:/bar/",
            "--stop-after-runs",
            "1",
            "--start",
            "2022-01-01T00:00:00-05:00",
        ],
    )
    sent_data = json.loads(get_last_request().body)
    assert sent_data["start"] == "2022-01-01T00:00:00-05:00"


def test_start_time_without_timezone_converts_to_have_tzinfo(
    run_line, ep_for_timer, monkeypatch
):
    # implicit timezone is localtime, but to handle mocking and testing
    # make timezone resolution return the time converted to EST

    # setup a patch that makes `astimezone` use EST always
    # and assert that no explicit timezone is passed
    est_tz = datetime.timezone(datetime.timedelta(hours=-5), name="EST")

    def fake_resolve(dt):
        assert dt is not None
        # this is *significantly* different from the real code at runtime
        # it assigns the EST timezone without a conversion (which is what the code
        # would do if the caller were in EST)
        return dt.replace(tzinfo=est_tz)

    monkeypatch.setattr(
        "globus_cli.commands.timer.create.transfer.resolve_start_time", fake_resolve
    )

    # argument and the expected transform
    start_arg = "2022-01-01T06:00:00"
    expect_value = "2022-01-01T06:00:00-05:00"

    run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{ep_for_timer}:/foo/",
            f"{ep_for_timer}:/bar/",
            "--stop-after-runs",
            "1",
            "--start",
            start_arg,
        ],
    )
    sent_data = json.loads(get_last_request().body)
    assert sent_data["start"] == expect_value


def test_timer_creation_rejects_data_access_requirement(
    run_line, ep_for_timer, non_ha_mapped_collection
):
    # explicit timezone is preserved in the formatted data sent to the service
    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{ep_for_timer}:/foo/",
            f"{non_ha_mapped_collection}:/bar/",
            "--interval",
            "60m",
            "--start",
            "2022-01-01T00:00:00-05:00",
        ],
        assert_exit_code=2,
    )
    assert "Unsupported operation." in result.stderr
