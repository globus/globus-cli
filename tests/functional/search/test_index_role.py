import json
import uuid

import pytest
import responses
from globus_sdk.testing import load_response_set


def _last_search_call():
    sent = None
    for call in responses.calls:
        if "search.api.globus.org" in call.request.url:
            sent = call
    assert sent is not None
    return sent


def test_index_role_list(run_line, get_identities_mocker):
    meta = load_response_set("cli.search").metadata

    sam_spade_username = "sam-spade@maltese.falcon"
    bruce_wayne_username = "bruce.wayne@gotham.city"
    get_identities_mocker.configure(
        [
            {"id": meta["primary_user_id"], "username": sam_spade_username},
            {"id": meta["secondary_user_id"], "username": bruce_wayne_username},
        ]
    )

    list_data = meta["index_role_list_data"]
    index_id = meta["index_id"]

    result = run_line(["globus", "search", "index", "role", "list", index_id])
    output_lines = result.output.splitlines()
    for role_id in list_data.keys():
        assert role_id in result.output
        assert result.output.count(role_id) == 1

    for role_id, data in list_data.items():
        role_name = data["role"]
        principal_key = data["value_meta_key"]
        if principal_key == "primary_user_id":
            principal = sam_spade_username
        elif principal_key == "secondary_user_id":
            principal = bruce_wayne_username
        elif principal_key == "group_id":
            principal = f"Globus Group ({meta['group_id']})"

        for line in output_lines:
            if role_id in line:
                assert role_name in line
                assert principal in line


@pytest.mark.parametrize(
    "principal_type, add_args",
    [
        ("username", []),
        ("identity_urn", []),
        ("identity_id", []),
        ("identity_id", ["--type", "identity"]),
        ("identity_urn", ["--type", "identity"]),
    ],
)
def test_index_role_create_identity(
    run_line, get_identities_mocker, principal_type, add_args
):
    meta = load_response_set("cli.search").metadata

    username = "sam-spade@maltese.falcon"
    get_identities_mocker.configure(
        [
            {"id": meta["primary_user_id"], "username": username},
            {"id": meta["secondary_user_id"]},
        ]
    )

    index_id = meta["index_id"]

    if principal_type == "username":
        principal = username
    elif principal_type == "identity_id":
        principal = meta["primary_user_id"]
    elif principal_type == "identity_urn":
        principal = f"urn:globus:auth:identity:{meta['primary_user_id']}"
    else:
        raise NotImplementedError(principal_type)

    run_line(
        ["globus", "search", "index", "role", "create", index_id, "writer", principal]
        + add_args
    )
    sent = _last_search_call().request
    assert sent.method == "POST"
    data = json.loads(sent.body)
    assert data["role_name"] == "writer"
    assert data["principal"] == f"urn:globus:auth:identity:{meta['primary_user_id']}"


@pytest.mark.parametrize(
    "principal_type, add_args",
    [
        ("group_urn", []),
        ("group_urn", ["--type", "group"]),
        ("group_id", ["--type", "group"]),
    ],
)
def test_index_role_create_group(
    run_line, get_identities_mocker, principal_type, add_args
):
    # NOTE: this test uses the same fixture data, but the fixtures are populated with
    # role information for an identity-related role
    # as a result, the response and output will not match, but the command should still
    # succeed and we can inspect the request sent
    # however, we need to include the get-identities data for the username lookup step
    meta = load_response_set("cli.search").metadata
    get_identities_mocker.configure(
        [{"id": meta["primary_user_id"]}, {"id": meta["secondary_user_id"]}]
    )

    index_id = meta["index_id"]

    if principal_type == "group_id":
        principal = meta["group_id"]
    elif principal_type == "group_urn":
        principal = f"urn:globus:groups:id:{meta['group_id']}"
    else:
        raise NotImplementedError(principal_type)

    run_line(
        ["globus", "search", "index", "role", "create", index_id, "admin", principal]
        + add_args
    )
    sent = _last_search_call().request
    assert sent.method == "POST"
    data = json.loads(sent.body)
    assert data["role_name"] == "admin"
    assert data["principal"] == f"urn:globus:groups:id:{meta['group_id']}"


@pytest.mark.parametrize(
    "cli_args, expect_message",
    [
        # won't resolve to an identity
        (["foo-bar"], "'foo-bar' was not resolvable to a globus identity"),
        (
            [
                "--type",
                "identity",
                "urn:globus:groups:id:a6de8802-6bce-4dd8-afa0-28dc38db5c77",
            ],
            "is not a valid username, identity UUID, or identity URN",
        ),
        (
            [
                "--type",
                "group",
                "urn:globus:auth:identity:25de0aed-aa83-4600-a1be-a62a910af116",
            ],
            "is not a valid group UUID or URN",
        ),
    ],
)
def test_index_role_create_invalid_args(
    run_line, get_identities_mocker, cli_args, expect_message
):
    # empty identity lookup results for the cases which do callout
    get_identities_mocker.configure_empty()
    index_id = str(uuid.uuid1())

    result = run_line(
        ["globus", "search", "index", "role", "create", index_id, "admin"] + cli_args,
        assert_exit_code=2,
    )
    assert expect_message in result.stderr


def test_index_role_delete(run_line):
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]
    role_id = meta["role_id"]

    result = run_line(
        ["globus", "search", "index", "role", "delete", index_id, role_id]
    )
    assert f"Successfully removed role {role_id}" in result.output
