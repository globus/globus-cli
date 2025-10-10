import json

import pytest
import responses
from globus_sdk.testing import load_response_set


# toggle between the (newer) 'gcs' variant and the 'bare' variant
@pytest.fixture(params=("gcs collection", "collection"))
def base_command(request):
    return f"globus {request.param} update"


@pytest.mark.parametrize("cid_key", ["mapped_collection_id", "guest_collection_id"])
def test_collection_update(run_line, add_gcs_login, base_command, cid_key):
    is_mapped = cid_key.startswith("mapped")

    meta = load_response_set("cli.collection_operations").metadata
    cid = meta[cid_key]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    ep_type_specific_opts = []
    if is_mapped:
        ep_type_specific_opts = ["--sharing-user-allow", ""]

    result = run_line(
        base_command.split()
        + [
            cid,
            "--description",
            "FooBar",
            "--keywords",
            "foo,bar",
        ]
        + ep_type_specific_opts
    )
    assert "success" in result.output

    sent = json.loads(responses.calls[-1].request.body)
    assert "description" in sent
    assert sent["description"] == "FooBar"
    assert "keywords" in sent
    assert sent["keywords"] == ["foo", "bar"]
    if is_mapped:
        assert "sharing_users_allow" in sent
        assert sent["sharing_users_allow"] == []


@pytest.mark.parametrize(
    "verify_str, verify_settings",
    [
        ("force", {"force_verify": True, "disable_verify": False}),
        ("disable", {"force_verify": False, "disable_verify": True}),
        ("default", {"force_verify": False, "disable_verify": False}),
    ],
)
@pytest.mark.parametrize("cid_key", ["mapped_collection_id", "guest_collection_id"])
def test_collection_update_verify_opts(
    run_line, add_gcs_login, base_command, verify_str, verify_settings, cid_key
):
    meta = load_response_set("cli.collection_operations").metadata
    cid = meta[cid_key]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    result = run_line(f"{base_command} {cid} --verify {verify_str}")
    assert "success" in result.output

    sent = json.loads(responses.calls[-1].request.body)
    for k, v in verify_settings.items():
        assert k in sent
        assert sent[k] == v


def test_collection_update_on_gcp(run_line, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["gcp_endpoint_id"]

    result = run_line(f"{base_command} {epid} --description foo", assert_exit_code=3)
    assert (
        f"Expected {epid} to be a collection ID.\n"
        "Instead, found it was of type 'Globus Connect Personal Mapped Collection'."
    ) in result.stderr
    assert (
        "Please run the following command instead:\n\n"
        f"    globus gcp update mapped {epid}"
    ) in result.stderr


def test_collection_update_on_gcsv5_host(run_line, base_command):
    meta = load_response_set("cli.collection_operations").metadata
    epid = meta["endpoint_id"]

    result = run_line(f"{base_command} {epid} --description foo", assert_exit_code=3)
    assert "success" not in result.output
    assert (
        f"Expected {epid} to be a collection ID.\n"
        "Instead, found it was of type 'Globus Connect Server v5 Endpoint'."
    ) in result.stderr
    assert "This operation is not supported on objects of this type." in result.stderr


def test_guest_collection_update_rejects_invalid_opts(
    run_line, add_gcs_login, base_command
):
    meta = load_response_set("cli.collection_operations").metadata
    cid = meta["guest_collection_id"]
    epid = meta["endpoint_id"]
    add_gcs_login(epid)

    result = run_line(
        f"{base_command} {cid} --sharing-user-allow ''",
        assert_exit_code=2,
    )
    assert "success" not in result.output
    assert (
        "Use of incompatible options with Globus Connect Server v5 Guest Collection"
        in result.stderr
    )
