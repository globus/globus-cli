import json
import uuid

import pytest
import responses
from globus_sdk._testing import load_response_set


def _last_search_call():
    sent = None
    for call in responses.calls:
        if "search.api.globus.org" in call.request.url:
            sent = call
    assert sent is not None
    return sent


def test_index_role_list(run_line):
    load_response_set("cli.multiuser_get_identities")
    meta = load_response_set("cli.search").metadata
    list_data = meta["index_role_list_data"]
    index_id = meta["index_id"]

    result = run_line(["globus", "search", "index", "role", "list", index_id])
    output_lines = result.output.splitlines()
    for role_id in list_data.keys():
        assert role_id in result.output
        assert result.output.count(role_id) == 1

    for role_id, data in list_data.items():
        role_name = data["role"]
        principal = data["value"]

        for line in output_lines:
            if role_id in line:
                assert role_name in line
                assert principal in line


@pytest.mark.parametrize(
    "cli_args",
    [
        ["foo@globusid.org"],
        ["urn:globus:auth:identity:25de0aed-aa83-4600-a1be-a62a910af116"],
        ["25de0aed-aa83-4600-a1be-a62a910af116"],
        ["25de0aed-aa83-4600-a1be-a62a910af116", "--type", "identity"],
        [
            "--type",
            "identity",
            "urn:globus:auth:identity:25de0aed-aa83-4600-a1be-a62a910af116",
        ],
    ],
)
def test_index_role_create_identity(run_line, cli_args):
    load_response_set("cli.multiuser_get_identities")
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    run_line(
        ["globus", "search", "index", "role", "create", index_id, "writer"] + cli_args
    )
    sent = _last_search_call().request
    assert sent.method == "POST"
    data = json.loads(sent.body)
    assert data["role_name"] == "writer"
    assert (
        data["principal"]
        == "urn:globus:auth:identity:25de0aed-aa83-4600-a1be-a62a910af116"
    )


@pytest.mark.parametrize(
    "cli_args",
    [
        ["urn:globus:groups:id:a6de8802-6bce-4dd8-afa0-28dc38db5c77"],
        [
            "--type",
            "group",
            "urn:globus:groups:id:a6de8802-6bce-4dd8-afa0-28dc38db5c77",
        ],
        ["--type", "group", "a6de8802-6bce-4dd8-afa0-28dc38db5c77"],
        [
            "--type",
            "group",
            "urn:globus:groups:id:a6de8802-6bce-4dd8-afa0-28dc38db5c77",
        ],
    ],
)
def test_index_role_create_group(run_line, cli_args):
    # NOTE: this test uses the same fixture data, but the fixtures are populated with
    # role information for an identity-related role
    # as a result, the response and output will not match, but the command should still
    # succeed and we can inspect the request sent
    # however, we need to include the get-identities data for the username lookup step
    load_response_set("cli.multiuser_get_identities")
    meta = load_response_set("cli.search").metadata
    index_id = meta["index_id"]

    run_line(
        ["globus", "search", "index", "role", "create", index_id, "admin"] + cli_args
    )
    sent = _last_search_call().request
    assert sent.method == "POST"
    data = json.loads(sent.body)
    assert data["role_name"] == "admin"
    assert (
        data["principal"] == "urn:globus:groups:id:a6de8802-6bce-4dd8-afa0-28dc38db5c77"
    )


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
def test_index_role_create_invalid_args(run_line, cli_args, expect_message):
    # empty identity lookup results for the cases which do callout
    responses.add(
        "GET",
        "https://auth.globus.org/v2/api/identities",
        headers={"Content-Type": "application/json"},
        json={"identities": []},
    )
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
