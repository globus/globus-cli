import datetime
import json
import uuid

import globus_sdk
import pytest
from globus_sdk._testing import (
    RegisteredResponse,
    get_last_request,
    load_response,
    load_response_set,
)
from globus_sdk.scopes import GCSCollectionScopeBuilder


def setup_timer_consent_tree_response(identity_id, *data_access_collection_ids):
    load_response(
        RegisteredResponse(
            service="auth",
            path=f"/v2/api/identities/{identity_id}/consents",
            method="GET",
            json={
                "consents": [
                    {
                        "scope_name": globus_sdk.TimerClient.scopes.timer,
                        "dependency_path": [100],
                        "id": 100,
                    },
                    {
                        "scope_name": (
                            "https://auth.globus.org/scopes/"
                            "actions.globus.org/transfer/transfer"
                        ),
                        "dependency_path": [100, 101],
                        "id": 101,
                    },
                    {
                        "scope_name": globus_sdk.TransferClient.scopes.all,
                        "dependency_path": [100, 101, 102],
                        "id": 102,
                    },
                ]
                + [
                    {
                        "scope_name": GCSCollectionScopeBuilder(name).data_access,
                        "dependency_path": [100, 101, 102, 1000 + idx],
                        "id": 1000 + idx,
                    }
                    for idx, name in enumerate(data_access_collection_ids)
                ]
            },
        )
    )


def make_non_ha_mapped_collection():
    mapped_collection_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
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
def non_ha_mapped_collection():
    return make_non_ha_mapped_collection()


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


@pytest.mark.parametrize("data_access_position", ["source", "destination", "both"])
@pytest.mark.parametrize(
    "has_matching_consent", ("neither", "source", "destination", "both")
)
def test_timer_creation_supports_data_access_on_source_or_dest(
    run_line, ep_for_timer, data_access_position, has_matching_consent
):
    if data_access_position == "source":
        src = make_non_ha_mapped_collection()
        dst = ep_for_timer
    elif data_access_position == "destination":
        src = ep_for_timer
        dst = make_non_ha_mapped_collection()
    elif data_access_position == "both":
        src = make_non_ha_mapped_collection()
        dst = make_non_ha_mapped_collection()
    else:
        raise NotImplementedError

    userinfo_meta = load_response_set("cli.foo_user_info").metadata
    identity_id = userinfo_meta["user_id"]
    # setup the consent tree response
    if has_matching_consent == "neither":
        setup_timer_consent_tree_response(identity_id)
    elif has_matching_consent == "source":
        setup_timer_consent_tree_response(identity_id, src)
    elif has_matching_consent == "destination":
        setup_timer_consent_tree_response(identity_id, dst)
    elif has_matching_consent == "both":
        setup_timer_consent_tree_response(identity_id, src, dst)
    else:
        raise NotImplementedError

    # determine what we expect to happen
    # successful submission or prompt?
    # if there is a prompt, what should it contain?
    appears_in_consent_prompt = []
    if has_matching_consent == "both":
        pass
    elif has_matching_consent == "neither":
        if data_access_position in ("source", "both"):
            appears_in_consent_prompt.append(src)
        if data_access_position in ("destination", "both"):
            appears_in_consent_prompt.append(dst)
    elif has_matching_consent == "source":
        if data_access_position in ("destination", "both"):
            appears_in_consent_prompt.append(dst)
    elif has_matching_consent == "destination":
        if data_access_position in ("source", "both"):
            appears_in_consent_prompt.append(src)
    else:
        raise NotImplementedError
    expect_consent_error = bool(appears_in_consent_prompt)

    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{src}:/foo/",
            f"{dst}:/bar/",
            "--interval",
            "60m",
        ],
        assert_exit_code=4 if expect_consent_error else 0,
    )
    if expect_consent_error:
        scope_opts = " ".join(
            f"--timer-data-access '{collection_id}'"
            for collection_id in appears_in_consent_prompt
        )
        assert f"globus session consent {scope_opts}" in result.output
    else:
        assert "Interval" in result.output
        req = get_last_request()
        assert req.url.startswith("https://timer")


def test_timer_creation_errors_on_data_access_with_client_creds(
    run_line, client_login, ep_for_timer
):
    src = make_non_ha_mapped_collection()
    dst = ep_for_timer

    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--recursive",
            f"{src}:/foo/",
            f"{dst}:/bar/",
            "--interval",
            "60m",
        ],
        assert_exit_code=2,
    )

    assert "Unsupported operation." in result.stderr
