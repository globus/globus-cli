import json
import uuid

import pytest
from globus_sdk.testing import get_last_request, load_response_set

# options with option value and expected value
# if expected value is not set, it will be copied from the option value
_OPTION_DICTS = {
    "display_name": {"opt": "--display-name", "key": "display_name", "val": "newname"},
    "description": {"opt": "--description", "key": "description", "val": "newtext"},
    "default_dir": {
        "opt": "--default-directory",
        "key": "default_directory",
        "val": "/share/",
    },
    "null_default_dir": {
        "opt": "--default-directory",
        "key": "default_directory",
        "val": "",
        "expected": None,
    },
    "organization": {"opt": "--organization", "key": "organization", "val": "neworg"},
    "department": {"opt": "--department", "key": "department", "val": "newdept"},
    "keywords": {"opt": "--keywords", "key": "keywords", "val": "new,key,words"},
    "contact_email": {"opt": "--contact-email", "key": "contact_email", "val": "a@b.c"},
    "contact_info": {"opt": "--contact-info", "key": "contact_info", "val": "newinfo"},
    "info_link": {"opt": "--info-link", "key": "info_link", "val": "http://a.b"},
    "force_encryption": {
        "opt": "--force-encryption",
        "key": "force_encryption",
        "val": None,
        "expected": True,
    },
    "disable_verify": {
        "opt": "--disable-verify",
        "key": "disable_verify",
        "val": None,
        "expected": True,
    },
    # server only options
    "myproxy_dn": {
        "opt": "--myproxy-dn",
        "key": "myproxy_dn",
        "val": "/dn",
    },
    "private": {
        "opt": "--private",
        "key": "public",
        "val": None,
        "expected": False,
    },
    "location": {
        "opt": "--location",
        "key": "location",
        "val": "1.1,2",
        "expected": "1.1,2",
    },
}

for optdict in _OPTION_DICTS.values():
    if "expected" not in optdict:
        optdict["expected"] = optdict["val"]


@pytest.mark.parametrize(
    "ep_type, options",
    [
        (
            "personal",
            [
                "display_name",
                "description",
                "default_dir",
                "organization",
                "department",
                "keywords",
                "contact_email",
                "contact_info",
                "info_link",
                "force_encryption",
                "disable_verify",
            ],
        ),
        (
            "share",
            [
                "display_name",
                "description",
                "default_dir",
                "organization",
                "department",
                "keywords",
                "contact_email",
                "contact_info",
                "info_link",
                "force_encryption",
                "disable_verify",
            ],
        ),
        (
            "server",
            [
                "display_name",
                "description",
                "default_dir",
                "organization",
                "department",
                "keywords",
                "contact_email",
                "contact_info",
                "info_link",
                "force_encryption",
                "disable_verify",
                "myproxy_dn",
                "private",
                "location",
            ],
        ),
        ("personal", ["private", "display_name", "description", "null_default_dir"]),
    ],
)
def test_general_options(run_line, ep_type, options):
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

    option_dicts = [_OPTION_DICTS[o] for o in options]

    # make and run the line
    line = ["globus", "endpoint", "update", epid, "-F", "json"]
    for item in option_dicts:
        line.append(item["opt"])
        if item["val"] is not None:
            line.append(item["val"])
    run_line(line)

    # get and confirm values which were sent as JSON
    sent_data = json.loads(get_last_request().body)
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
        "--myproxy-dn /dn",
        "--myproxy-server mpsrv.example.com",
        "--oauth-server oasrv.example.com",
        "--location 1,1",
    ]
    for opt in options:
        result = run_line(
            f"globus endpoint update {epid} {opt} ",
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
            f"globus endpoint update {epid} {opt} ",
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
