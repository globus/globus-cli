import json
import urllib.parse
import uuid

import pytest
import responses
from globus_sdk.testing import (
    RegisteredResponse,
    load_response,
    load_response_set,
    register_response_set,
)


@pytest.fixture(autouse=True, scope="session")
def _register_get_group_responses():
    group_id = "efdab3ca-cff1-11e4-9b86-123139260d4e"

    register_response_set(
        "get_group?include=memberships",
        {
            "default": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "json": {
                    "description": "Ipso facto",
                    "enforce_session": False,
                    "group_type": "regular",
                    "id": group_id,
                    "memberships": [
                        {
                            "group_id": group_id,
                            "identity_id": "ae332d86-d274-11e5-b885-b31714a110e9",
                            "membership_fields": {
                                "department": "Globus Testing",
                                "email": "sirosen@globus.org",
                                "field_of_science": "CS",
                                "institution": "Computation Institute",
                                "phone": "867-5309",
                            },
                            "role": "admin",
                            "status": "active",
                            "username": "sirosen@globusid.org",
                        },
                        {
                            "group_id": group_id,
                            "identity_id": "508e5ef6-cb9b-11e5-abe1-431ce3f42be1",
                            "membership_fields": {},
                            "role": "member",
                            "status": "invited",
                            "username": "sirosen@xsede.org",
                        },
                        {
                            "group_id": group_id,
                            "identity_id": "ae2f7f60-d274-11e5-b879-afc598dd59d4",
                            "membership_fields": {
                                "institution": "University of Chicago",
                                "name": "Bryce Allen",
                                "department": "Globus",
                            },
                            "role": "member",
                            "status": "active",
                            "username": "ballen@globusid.org",
                        },
                        {
                            "group_id": group_id,
                            "identity_id": "b0e8f24a-d274-11e5-8c98-8fd1e61c0a76",
                            "membership_fields": {
                                "current_project_name": "Petrel support",
                                "department": "UChicago",
                            },
                            "role": "member",
                            "status": "rejected",
                            "username": "smartin@globusid.org",
                        },
                        {
                            "group_id": group_id,
                            "identity_id": "6b487878-d2a1-11e5-b689-a7dd99513a65",
                            "membership_fields": {
                                "department": (
                                    "Columbia University department "
                                    "of Witchcraft and History"
                                ),
                            },
                            "role": "member",
                            "status": "active",
                            "username": "jss2253@columbia.edu",
                        },
                        {
                            "group_id": group_id,
                            "identity_id": "ae2a1750-d274-11e5-b867-e74762c29f57",
                            "membership_fields": {},
                            "role": "member",
                            "status": "invited",
                            "username": "bjmc@globusid.org",
                        },
                    ],
                    "name": "Claptrap Presents Claptrap's Rough Riders",
                    "parent_id": None,
                    "policies": {
                        "authentication_assurance_timeout": 28800,
                        "group_members_visibility": "managers",
                        "group_visibility": "private",
                        "is_high_assurance": False,
                        "join_requests": False,
                        "signup_fields": [],
                    },
                    "session_limit": 28800,
                    "session_timeouts": {
                        "ae341a98-d274-11e5-b888-dbae3a8ba545": {
                            "expire_time": "2022-02-08T06:05:54+00:00",
                            "expires_in": 0,
                        }
                    },
                },
                "metadata": {
                    "group_id": group_id,
                    "known_members": [
                        {
                            "role": "admin",
                            "status": "active",
                            "username": "sirosen@globusid.org",
                        },
                        {
                            "role": "member",
                            "status": "invited",
                            "username": "bjmc@globusid.org",
                        },
                        {
                            "role": "member",
                            "status": "rejected",
                            "username": "smartin@globusid.org",
                        },
                    ],
                },
            }
        },
    )


@pytest.fixture(autouse=True, scope="session")
def _register_group_action_responses():
    group_id = "efdab3ca-cff1-11e4-9b86-123139260d4e"
    identity_id = "00000000-0000-0000-0000-000000000001"
    username = "foo@example.org"

    common_action_metadata = {
        "group_id": group_id,
        "identity_id": identity_id,
        "username": username,
    }

    # seed with relatively uniform data
    response_sets = {}
    for action in ["approve", "reject", "invite"]:
        status = "active"
        if action == "reject":
            status = "rejected"
        elif action == "invite":
            status = "invited"
        response_sets[action] = {
            "default": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "method": "POST",
                "json": {
                    action: [
                        {
                            "group_id": group_id,
                            "identity_id": identity_id,
                            "username": username,
                            "role": "member",
                            "status": status,
                        }
                    ]
                },
                "metadata": common_action_metadata,
            },
            "error": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "method": "POST",
                "json": {
                    "errors": {
                        action: [
                            {
                                "code": "ERROR_ERROR_IT_IS_AN_ERROR",
                                "identity_id": identity_id,
                                "detail": "Domo arigato, Mr. Roboto",
                            }
                        ]
                    },
                },
                "metadata": common_action_metadata,
            },
            "error_nodetail": {
                "service": "groups",
                "path": f"/v2/groups/{group_id}",
                "method": "POST",
                "json": {
                    "errors": {"foo": "bar"},
                },
                "metadata": common_action_metadata,
            },
        }
    # the response sets could be customized further here, prior to...
    # ...registration of response sets
    for action in ["approve", "reject", "invite"]:
        register_response_set(
            f"group_member_{action}",
            response_sets[action],
            metadata=common_action_metadata,
        )


def test_group_member_add(run_line):
    meta = load_response_set("cli.groups").metadata
    group = meta["group1_id"]
    member = meta["user1_id"]
    result = run_line(f"globus group member add {group} {member}")
    username = meta["user1_username"]
    assert member in result.output
    assert username in result.output
    assert group in result.output
    sent_data = json.loads(responses.calls[-1].request.body)
    assert "add" in sent_data
    assert len(sent_data["add"]) == 1
    assert sent_data["add"][0]["identity_id"] == member


def test_group_member_add_failure(run_line):
    meta = load_response_set("cli.groups").metadata
    group = meta["group1_id"]
    bad_identity = "NOT_A_VALID_USER"
    result = run_line(
        f"globus group member add {group} {bad_identity}", assert_exit_code=2
    )
    assert "Error" in result.stderr
    assert bad_identity in result.stderr


def test_group_member_add_already_in_group(run_line):
    meta = load_response_set("cli.groups").metadata
    group = meta["group_already_added_user_id"]
    member = meta["user1_id"]
    result = run_line(f"globus group member add {group} {member}", assert_exit_code=1)
    assert "already an active member of the group" in result.stderr


def test_group_member_remove(run_line):
    meta = load_response_set("cli.groups").metadata
    group = meta["group_remove_id"]
    member = meta["user1_id"]
    username = meta["user1_username"]
    result = run_line(f"globus group member remove {group} {member}")
    assert member in result.output
    assert username in result.output
    assert group in result.output
    sent_data = json.loads(responses.calls[-1].request.body)
    assert "remove" in sent_data
    assert len(sent_data["remove"]) == 1
    assert sent_data["remove"][0]["identity_id"] == member


def test_group_member_already_removed(run_line):
    meta = load_response_set("cli.groups").metadata
    group = meta["group_user_remove_error"]
    member = meta["user1_id"]
    result = run_line(
        f"globus group member remove {group} {member}", assert_exit_code=1
    )
    assert "Identity has no membership in group" in result.stderr


@pytest.mark.parametrize("action", ("accept", "decline"))
@pytest.mark.parametrize("with_id_arg", (True, False))
def test_group_invite_basic(run_line, action, with_id_arg):
    group_id = "ee49e222-d007-11e4-8b51-22000aa51e6e"
    identity_id = "00000000-0000-0000-0000-000000000001"
    load_response(
        RegisteredResponse(
            service="groups",
            path=f"/v2/groups/{group_id}",
            json={
                "description": "Un film Italiano muy bien conocido",
                "enforce_session": False,
                "group_type": "regular",
                "id": group_id,
                "my_memberships": [
                    {
                        "group_id": group_id,
                        "identity_id": identity_id,
                        "membership_fields": {},
                        "role": "member",
                        "status": "invited",
                        "username": "test_user1",
                    },
                ],
                "name": "La Dolce Vita",
                "parent_id": None,
                "policies": {
                    "authentication_assurance_timeout": 28800,
                    "group_members_visibility": "managers",
                    "group_visibility": "authenticated",
                    "is_high_assurance": False,
                    "join_requests": False,
                    "signup_fields": [],
                },
                "session_limit": 28800,
                "session_timeouts": {},
            },
        )
    )
    load_response(
        RegisteredResponse(
            service="groups",
            path=f"/v2/groups/{group_id}",
            method="POST",
            json={
                action: [
                    {
                        "group_id": group_id,
                        "identity_id": identity_id,
                        "username": "test_user1",
                        "role": "member",
                        "status": "active",
                    }
                ]
            },
        )
    )

    add_args = []
    if with_id_arg:
        add_args = ["--identity", identity_id]
    result = run_line(["globus", "group", "invite", action, group_id] + add_args)
    assert identity_id in result.output

    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == identity_id


@pytest.mark.parametrize("action", ("accept", "decline"))
@pytest.mark.parametrize("error_detail_present", (True, False))
def test_group_invite_failure(run_line, action, error_detail_present):
    group_id = "ee49e222-d007-11e4-8b51-22000aa51e6e"
    identity_id = "00000000-0000-0000-0000-000000000001"
    load_response(
        RegisteredResponse(
            service="groups",
            path=f"/v2/groups/{group_id}",
            json={
                "description": "Un film Italiano muy bien conocido",
                "enforce_session": False,
                "group_type": "regular",
                "id": group_id,
                "my_memberships": [
                    {
                        "group_id": group_id,
                        "identity_id": identity_id,
                        "membership_fields": {},
                        "role": "member",
                        "status": "invited",
                        "username": "test_user1",
                    },
                ],
                "name": "La Dolce Vita",
                "parent_id": None,
                "policies": {
                    "authentication_assurance_timeout": 28800,
                    "group_members_visibility": "managers",
                    "group_visibility": "authenticated",
                    "is_high_assurance": False,
                    "join_requests": False,
                    "signup_fields": [],
                },
                "session_limit": 28800,
                "session_timeouts": {},
            },
        )
    )

    error_detail = (
        {"detail": "Domo arigato, Mr. Roboto"} if error_detail_present else {}
    )
    load_response(
        RegisteredResponse(
            service="groups",
            path=f"/v2/groups/{group_id}",
            method="POST",
            json={
                action: [],
                "errors": {
                    action: [
                        {
                            "code": "ERROR_ERROR_IT_IS_AN_ERROR",
                            "identity_id": identity_id,
                            **error_detail,
                        }
                    ]
                },
            },
        )
    )

    result = run_line(
        ["globus", "group", "invite", action, group_id], assert_exit_code=1
    )
    assert "Error" in result.stderr
    if error_detail_present:
        assert "Domo arigato" in result.stderr
    else:
        assert f"Could not {action} invite" in result.stderr

    # the request sent was as expected
    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == identity_id


@pytest.mark.parametrize(
    "add_args,expect_data",
    [
        ([], []),
        (
            ["--fields", "institution,department"],
            [
                "Computation Institute",
                "University of Chicago",
                "Witchcraft and History",
            ],
        ),
        (
            ["--fields", "current_project_name"],
            ["Petrel support"],
        ),
    ],
)
def test_group_member_list(run_line, add_args, expect_data):
    meta = load_response("get_group?include=memberships").metadata
    result = run_line(
        ["globus", "group", "member", "list", meta["group_id"]] + add_args
    )
    for item in expect_data:
        assert item in result.output
    for item in meta["known_members"]:
        username, role, status = item["username"], item["role"], item["status"]
        matching_lines = [
            line
            for line in result.output.splitlines()
            if username in line and role in line and status in line
        ]
        assert len(matching_lines) == 1


def test_group_member_list_rejects_unknown_field(run_line):
    dummy_id = uuid.UUID(int=0)
    result = run_line(
        f"globus group member list {dummy_id} --fields country,foo",
        assert_exit_code=2,
    )
    assert "the values ['foo'] were not valid choices" in result.stderr


@pytest.mark.parametrize("action", ["approve", "reject", "invite"])
def test_group_member_simple_action_success(run_line, action):
    meta = load_response(f"group_member_{action}").metadata
    group = meta["group_id"]
    member = meta["identity_id"]
    username = meta["username"]
    result = run_line(f"globus group member {action} {group} {member}")
    assert member in result.output
    assert username in result.output
    assert group in result.output
    sent_data = json.loads(responses.calls[-1].request.body)
    assert action in sent_data
    assert len(sent_data[action]) == 1
    assert sent_data[action][0]["identity_id"] == member


@pytest.mark.parametrize("action", ["approve", "reject", "invite"])
@pytest.mark.parametrize("error_detail", [True, False])
def test_group_member_simple_action_error(run_line, action, error_detail):
    meta = load_response(
        f"group_member_{action}", case="error" if error_detail else "error_nodetail"
    ).metadata
    group = meta["group_id"]
    member = meta["identity_id"]
    result = run_line(
        f"globus group member {action} {group} {member}", assert_exit_code=1
    )
    assert "Error" in result.stderr
    if error_detail:
        assert "Domo arigato" in result.stderr
    else:
        if action == "approve":
            assert "Could not approve the user" in result.stderr
        elif action == "reject":
            assert "Could not reject the user" in result.stderr
        elif action == "invite":
            assert "Could not invite the user" in result.stderr


def test_group_member_invite_by_username_no_such_user(run_line, get_identities_mocker):
    get_identities_mocker.configure_empty()
    meta = load_response("group_member_invite").metadata
    username = meta["username"]
    group_id = meta["group_id"]
    result = run_line(
        f"globus group member invite {group_id} {username}", assert_exit_code=2
    )
    assert "Couldn't determine identity from user value:" in result.stderr
    assert username in result.stderr


@pytest.mark.parametrize("w_provision_option", (True, False))
def test_group_member_invite_by_username(
    run_line, w_provision_option, get_identities_mocker
):
    meta = load_response("group_member_invite").metadata
    username = meta["username"]
    identity_id = meta["identity_id"]
    group_id = meta["group_id"]
    get_identities_mocker.configure_one(username=username, id=identity_id)

    add_args = []
    if w_provision_option:
        add_args = ["--provision-identity"]
    run_line(["globus", "group", "member", "invite", group_id, username] + add_args)
    assert len(responses.calls) >= 2
    auth_request = next(
        call.request
        for call in responses.calls
        if call.request.url.startswith("https://auth.globus.org/v2/api/identities")
    )
    groups_request = next(
        call.request
        for call in responses.calls
        if call.request.url.startswith("https://groups.api.globus.org/")
    )

    auth_url = urllib.parse.urlparse(auth_request.url)
    if w_provision_option:
        auth_query = urllib.parse.parse_qs(auth_url.query)
        assert "provision" in auth_query
        assert auth_query["provision"] == ["true"]
    else:
        auth_query = urllib.parse.parse_qs(auth_url.query)
        assert "provision" in auth_query
        assert auth_query["provision"] == ["false"]

    sent_data = json.loads(groups_request.body)
    assert "invite" in sent_data
    assert len(sent_data["invite"]) == 1
    invite_data = sent_data["invite"][0]
    assert invite_data["identity_id"] == identity_id
