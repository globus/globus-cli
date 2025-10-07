import datetime
import itertools
import json
import uuid

import globus_sdk
import pytest
import requests
import responses
from globus_sdk._testing import RegisteredResponse, get_last_request, load_response
from globus_sdk.config import get_service_url
from globus_sdk.scopes import GCSCollectionScopeBuilder


@pytest.fixture
def resolve_times_to_utc(monkeypatch):
    # implicit timezone is localtime, but to handle mocking and testing
    # make timezone resolution return the time converted to UTC
    def fake_resolve(dt):
        if dt is None:
            return globus_sdk.MISSING
        if dt.tzinfo is not None:
            return dt
        # this is *significantly* different from the real code at runtime
        return dt.replace(tzinfo=datetime.timezone.utc)

    from globus_cli.commands.timer.create import _common as module

    monkeypatch.setattr(module, "_to_local_tz", fake_resolve)


def setup_timer_consent_tree_response(identity_id, *data_access_collection_ids):
    _dummy_consent_fields = {
        "allows_refresh": True,
        "atomically_revocable": False,
        "auto_approved": False,
        "client": str(uuid.UUID(int=1)),
        "created": "1970-01-01T00:00:00.000000+00:00",
        "effective_identity": str(uuid.UUID(int=2)),
        "last_used": "1970-01-01T00:00:00.000000+00:00",
        "status": "approved",
        "updated": "1970-01-01T00:00:00.000000+00:00",
    }
    load_response(
        RegisteredResponse(
            service="auth",
            path=f"/v2/api/identities/{identity_id}/consents",
            method="GET",
            json={
                "consents": [
                    {
                        "scope_name": globus_sdk.TimerClient.scopes.timer,
                        "scope": str(uuid.uuid1()),
                        "dependency_path": [100],
                        "id": 100,
                        **_dummy_consent_fields,
                    },
                    {
                        "scope_name": globus_sdk.TransferClient.scopes.all,
                        "scope": str(uuid.uuid1()),
                        "dependency_path": [100, 101],
                        "id": 101,
                        **_dummy_consent_fields,
                    },
                ]
                + [
                    {
                        "scope_name": GCSCollectionScopeBuilder(name).data_access,
                        "scope": str(uuid.uuid1()),
                        "dependency_path": [100, 101, 1000 + idx],
                        "id": 1000 + idx,
                        **_dummy_consent_fields,
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
    return mapped_collection_id


@pytest.fixture
def non_ha_mapped_collection():
    return make_non_ha_mapped_collection()


@pytest.fixture
def ep_for_timer():
    load_response(globus_sdk.TimerClient.create_timer)
    load_response(globus_sdk.TransferClient.get_submission_id)
    ep_meta = load_response(globus_sdk.TransferClient.get_endpoint).metadata
    ep_id = ep_meta["endpoint_id"]
    return ep_id


@pytest.mark.parametrize(
    "extra_args",
    [
        ["--interval", "600s"],
        ["--stop-after-runs", "1"],
    ],
)
def test_create_timer_simple(run_line, ep_for_timer, extra_args):
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
    transfer_body = sent_data["timer"]["body"]
    assert transfer_body["DATA_TYPE"] == "transfer"
    assert isinstance(transfer_body["DATA"], list)
    assert len(transfer_body["DATA"]) == 1
    assert transfer_body["DATA"][0]["DATA_TYPE"] == "transfer_item"
    assert transfer_body["DATA"][0]["source_path"] == "/file1"
    assert transfer_body["DATA"][0]["destination_path"] == "/file2"


def test_create_endless_timer(run_line, ep_for_timer):
    """Create a timer which has no end condition."""
    create_route = f"{get_service_url('timer')}v2/timer"
    patched_response = requests.post(create_route).json()
    patched_response["timer"]["schedule"]["end"] = None

    responses.replace("POST", create_route, json=patched_response)

    resp = run_line(
        f"globus timer create transfer {ep_for_timer}:/ {ep_for_timer}:/ --interval 1m"
    )

    assert "Schedule" in resp.output


def test_create_timer_batch_data(run_line, ep_for_timer):
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
    transfer_body = sent_data["timer"]["body"]
    assert transfer_body["DATA_TYPE"] == "transfer"
    assert isinstance(transfer_body["DATA"], list)
    assert len(transfer_body["DATA"]) == 2
    assert transfer_body["DATA"][0]["DATA_TYPE"] == "transfer_item"
    assert transfer_body["DATA"][1]["DATA_TYPE"] == "transfer_item"
    assert transfer_body["DATA"][0]["source_path"] == "abc"
    assert transfer_body["DATA"][0]["destination_path"] == "/def"
    assert transfer_body["DATA"][1]["source_path"] == "/xyz"
    assert transfer_body["DATA"][1]["destination_path"] == "p/q/r"


@pytest.mark.parametrize("option", ("--recursive", "--no-recursive"))
def test_recursive_and_batch_exclusive(run_line, option):
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
            option,
            "--batch",
            "-",
        ],
        assert_exit_code=2,
    )
    assert f"You cannot use `{option}` in addition to `--batch`" in result.stderr


def test_create_timer_requires_some_pathargs(run_line):
    ep_id = str(uuid.UUID(int=1))

    result = run_line(
        ["globus", "timer", "create", "transfer", ep_id, ep_id, "--interval", "1800s"],
        assert_exit_code=2,
    )
    assert (
        "Transfer requires either `SOURCE_PATH` and `DEST_PATH` or `--batch`"
        in result.stderr
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
    assert "`--interval` is required unless `--stop-after-runs=1`" in result.stderr


def test_stop_conditions_are_mutex(run_line):
    ep_id = str(uuid.UUID(int=1))
    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--stop-after-runs",
            "1",
            "--stop-after-date",
            "2021-01-01T00:00:00",
            f"{ep_id}:/foo/",
            f"{ep_id}:/bar/",
        ],
        assert_exit_code=2,
    )
    assert "mutually exclusive" in result.stderr


def test_legacy_delete_and_delete_destination_are_mutex(run_line):
    ep_id = str(uuid.UUID(int=1))
    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--delete",
            "--delete-destination-extra",
            f"{ep_id}:/foo/",
            f"{ep_id}:/bar/",
            "--stop-after-runs=1",
        ],
        assert_exit_code=2,
    )
    assert "mutually exclusive" in result.stderr


def test_timer_creation_legacy_delete_flag_deprecation_warning(run_line, ep_for_timer):
    result = run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--delete",
            f"{ep_for_timer}:/foo/",
            f"{ep_for_timer}:/bar/",
            "--stop-after-runs=1",
        ],
        assert_exit_code=0,
    )
    assert "`--delete` has been deprecated" in result.stderr


def test_timer_uses_once_schedule_if_stop_after_is_one(run_line, ep_for_timer):
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
    sent_timer = sent_data["timer"]
    schedule = sent_timer["schedule"]
    assert schedule["type"] == "once"


def test_start_time_allows_timezone(run_line, ep_for_timer, resolve_times_to_utc):
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
    sent_timer = sent_data["timer"]
    schedule = sent_timer["schedule"]
    assert schedule["type"] == "once"
    assert schedule["datetime"] == "2022-01-01T00:00:00-05:00"


def test_start_time_without_timezone_converts_to_have_tzinfo(
    run_line, ep_for_timer, monkeypatch, resolve_times_to_utc
):
    # argument and the expected transform
    # note that this is really just running the fake tz resolver
    start_arg = "2022-01-01T06:00:00"
    expect_value = "2022-01-01T06:00:00+00:00"

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
    sent_timer = sent_data["timer"]
    schedule = sent_timer["schedule"]
    assert schedule["type"] == "once"
    assert schedule["datetime"] == expect_value


@pytest.mark.parametrize("data_access_position", ["source", "destination", "both"])
@pytest.mark.parametrize(
    "has_matching_consent", ("neither", "source", "destination", "both")
)
def test_timer_creation_supports_data_access_on_source_or_dest(
    run_line,
    logged_in_user_id,
    userinfo_mocker,
    ep_for_timer,
    data_access_position,
    has_matching_consent,
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

    userinfo_meta = userinfo_mocker.configure_unlinked(sub=logged_in_user_id).metadata
    identity_id = userinfo_meta["sub"]
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
        assert "every 604800 seconds" in result.output
        req = get_last_request()
        assert req.url.startswith("https://timer")


def test_timer_creation_errors_on_data_access_with_client_creds(
    run_line, client_login, ep_for_timer
):
    src = make_non_ha_mapped_collection()
    dst = ep_for_timer

    setup_timer_consent_tree_response("fake_client_id", src)

    run_line(
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
    )

    req = get_last_request()
    assert req.url.startswith("https://timer")


@pytest.mark.parametrize(
    "deletion_option,recursion_option,expected_error",
    (
        ("--delete-destination-extra", "--recursive", ""),
        ("--delete-destination-extra", "", ""),
        (
            "--delete-destination-extra",
            "--no-recursive",
            (
                "The `--delete-destination-extra` option cannot be specified with "
                "`--no-recursive`."
            ),
        ),
        ("--delete", "--recursive", ""),
        ("--delete", "", ""),
        (
            "--delete",
            "--no-recursive",
            "The `--delete` option cannot be specified with `--no-recursive`.",
        ),
    ),
)
def test_timer_creation_delete_flag_requires_recursion(
    run_line,
    client_login,
    ep_for_timer,
    deletion_option,
    recursion_option,
    expected_error,
):
    base_cmd = f"globus timer create transfer {ep_for_timer}:/foo/ {ep_for_timer}:/bar/"
    options_list = ("--interval 60m", deletion_option, recursion_option)
    options = " ".join(op for op in options_list if op is not None)

    exit_code = 0 if not expected_error else 2
    resp = run_line(f"{base_cmd} {options}", assert_exit_code=exit_code)

    assert expected_error in resp.stderr


def test_timer_creation_supports_filter_rules(run_line, ep_for_timer):
    """
    Confirm that `--include/--exclude` ordering is preserved.
    """
    filter_opts = [
        ("--exclude", "foo"),
        ("--include", "bar"),
        ("--include", "baz"),
        ("--exclude", "qux"),
    ]
    expected_filter_rules = [
        {
            "DATA_TYPE": "filter_rule",
            "method": opt[0].lstrip("-"),
            "name": opt[1],
            "type": "file",
        }
        for opt in filter_opts
    ]

    run_line(
        [
            "globus",
            "timer",
            "create",
            "transfer",
            "--stop-after-runs",
            "1",
            "--recursive",
            f"{ep_for_timer}:/",
            f"{ep_for_timer}:/",
            *itertools.chain(*filter_opts),
        ]
    )

    sent_data = json.loads(get_last_request().body)
    transfer_body = sent_data["timer"]["body"]
    assert transfer_body["filter_rules"] == expected_filter_rules
