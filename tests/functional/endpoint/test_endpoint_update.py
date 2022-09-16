import json
import uuid

import pytest
import responses
from globus_sdk._testing import load_response_set


@pytest.mark.parametrize("ep_type", ["personal", "share", "server"])
def test_general_options(run_line, ep_type):
    """
    Runs endpoint update with parameters allowed for all endpoint types
    Confirms all endpoint types are successfully updated
    """
    meta = load_response_set("cli.endpoint_operations").metadata
    if ep_type == "personal":
        epid = meta["gcp_endpoint_id"]
    elif ep_type == "share":
        epid = meta["share_id"]
    else:
        epid = meta["endpoint_id"]

    # options with option value and expected value
    # if expected value is not set, it will be copied from the option value
    option_dicts = [
        {"opt": "--display-name", "key": "display_name", "val": "newname"},
        {"opt": "--description", "key": "description", "val": "newtext"},
        {"opt": "--default-directory", "key": "default_directory", "val": "/share/"},
        {"opt": "--organization", "key": "organization", "val": "neworg"},
        {"opt": "--department", "key": "department", "val": "newdept"},
        {"opt": "--keywords", "key": "keywords", "val": "new,key,words"},
        {"opt": "--contact-email", "key": "contact_email", "val": "a@b.c"},
        {"opt": "--contact-info", "key": "contact_info", "val": "newinfo"},
        {"opt": "--info-link", "key": "info_link", "val": "http://a.b"},
        {
            "opt": "--force-encryption",
            "key": "force_encryption",
            "val": None,
            "expected": True,
        },
        {
            "opt": "--disable-verify",
            "key": "disable_verify",
            "val": None,
            "expected": True,
        },
    ]
    if ep_type == "server":
        option_dicts.extend(
            [
                {"opt": "--myproxy-dn", "key": "myproxy_dn", "val": "/dn"},
                {
                    "opt": "--myproxy-server",
                    "key": "myproxy_server",
                    "val": "srv.example.com",
                },
                {"opt": "--private", "key": "public", "val": None, "expected": False},
                {
                    "opt": "--location",
                    "key": "location",
                    "val": "1.1,2",
                    "expected": "1.1,2",
                },
            ]
        )

    for x in option_dicts:
        if "expected" not in x:
            x["expected"] = x["val"]

    # make and run the line
    line = ["globus", "endpoint", "update", epid, "-F", "json"]
    for item in option_dicts:
        line.append(item["opt"])
        if item["val"]:
            line.append(item["val"])
    run_line(" ".join(line))

    # get and confirm values which were sent as JSON
    sent_data = json.loads(responses.calls[-1].request.body)
    for item in option_dicts:
        assert item["expected"] == sent_data[item["key"]]


@pytest.mark.parametrize("ep_type", ["personal", "share"])
def test_invalid_gcs_only_options(run_line, ep_type):
    """
    For all GCS only options, tries to update a GCP and shared endpoint
    Confirms invalid options are caught at the CLI level rather than API
    """
    meta = load_response_set("cli.endpoint_operations").metadata
    if ep_type == "personal":
        epid = meta["gcp_endpoint_id"]
    elif ep_type == "share":
        epid = meta["share_id"]
    else:
        raise NotImplementedError
    options = [
        "--public",
        "--private",
        "--myproxy-dn /dn",
        "--myproxy-server mpsrv.example.com",
        "--oauth-server oasrv.example.com",
        "--location 1,1",
    ]
    for opt in options:
        result = run_line(
            (f"globus endpoint update {epid} {opt} "),
            assert_exit_code=2,
        )
        assert "Globus Connect Server" in result.stderr


def test_invalid_managed_only_options(run_line):
    """
    For all managed only options, tries to update a GCS endpoint
    Confirms invalid options are caught at the CLI level rather than AP
    """
    meta = load_response_set("cli.endpoint_operations").metadata
    epid = meta["endpoint_id"]

    options = [
        "--network-use custom",
        "--max-concurrency 2",
        "--preferred-concurrency 1",
        "--max-parallelism 2",
        "--preferred-parallelism 1",
    ]
    for opt in options:
        result = run_line(
            (f"globus endpoint update {epid} {opt} "),
            assert_exit_code=2,
        )
        assert "managed endpoints" in result.stderr


def test_mutex_options(run_line):
    subid = str(uuid.uuid1())
    epid = str(uuid.uuid1())
    options = [
        "--default-directory /foo/ --no-default-directory",
        f"--subscription-id {subid} --no-managed",
    ]
    for opts in options:
        result = run_line(
            f"globus endpoint update {epid} {opts}",
            assert_exit_code=2,
        )
        assert "mutually exclusive" in result.stderr
