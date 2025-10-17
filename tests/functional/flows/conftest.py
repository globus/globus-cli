from __future__ import annotations

import datetime
import random
import typing as t
import uuid

import pytest
from globus_sdk.testing import register_response_set
from responses import matchers

OWNER_ID = "e061df5a-b7b9-4578-a73b-6d4a4edfd66e"


# this builder is mostly copied from globus-sdk tests with minimal changes
#
# TODO: find a better way to share the paginated fixture data generation between these
# two projects
def generate_hello_world_example_flow(
    n: int, *, title: str | None = None
) -> dict[str, t.Any]:
    flow_id = str(uuid.UUID(int=n))
    base_time = datetime.datetime.fromisoformat("2021-10-18T19:19:35.967289+00:00")
    updated_at = created_at = base_time + datetime.timedelta(days=n)
    flow_user_scope = (
        f"https://auth.globus.org/scopes/{flow_id}/"
        f"flow_{flow_id.replace('-', '_')}_user"
    )

    return {
        "action_url": f"https://flows.automate.globus.org/flows/{flow_id}",
        "administered_by": [],
        "api_version": "1.0",
        "created_at": created_at.isoformat(),
        "created_by": f"urn:globus:auth:identity:{OWNER_ID}",
        "definition": {
            "StartAt": "HelloWorld",
            "States": {
                "HelloWorld": {
                    "ActionScope": (
                        "https://auth.globus.org/scopes/actions.globus.org/hello_world"
                    ),
                    "ActionUrl": "https://actions.globus.org/hello_world",
                    "End": True,
                    "Parameters": {"echo_string": "Hello, World."},
                    "ResultPath": "$.Result",
                    "Type": "Action",
                }
            },
        },
        "description": "A simple Flow...",
        "flow_administrators": [],
        "flow_owner": f"urn:globus:auth:identity:{OWNER_ID}",
        "flow_starters": [],
        "flow_url": f"https://flows.automate.globus.org/flows/{flow_id}",
        "flow_viewers": [],
        "globus_auth_scope": flow_user_scope,
        "globus_auth_username": f"{flow_id}@clients.auth.globus.org",
        "id": str(flow_id),
        "input_schema": {
            "additionalProperties": False,
            "properties": {
                "echo_string": {"description": "The string to echo", "type": "string"},
                "sleep_time": {"type": "integer"},
            },
            "required": ["echo_string", "sleep_time"],
            "type": "object",
        },
        "keywords": [],
        "log_supported": True,
        "principal_urn": f"urn:globus:auth:identity:{flow_id}",
        "runnable_by": [],
        "subtitle": "",
        "synchronous": False,
        "title": title or f"Hello, World (Example {n})",
        "types": ["Action"],
        "updated_at": updated_at.isoformat(),
        "user_role": "flow_viewer",
        "visible_to": [],
    }


@pytest.fixture(autouse=True, scope="session")
def setup_paginated_responses() -> None:
    register_response_set(
        "flows_list_paginated",
        {
            "page0": {
                "service": "flows",
                "path": "/flows",
                "json": {
                    "flows": [generate_hello_world_example_flow(i) for i in range(20)],
                    "limit": 20,
                    "has_next_page": True,
                    "marker": "fake_marker_0",
                },
                "match": [matchers.query_param_matcher({"orderby": "updated_at DESC"})],
            },
            "page1": {
                "service": "flows",
                "path": "/flows",
                "json": {
                    "flows": [
                        generate_hello_world_example_flow(i) for i in range(20, 40)
                    ],
                    "limit": 20,
                    "has_next_page": True,
                    "marker": "fake_marker_1",
                },
                "match": [
                    matchers.query_param_matcher(
                        {"orderby": "updated_at DESC", "marker": "fake_marker_0"}
                    )
                ],
            },
            "page2": {
                "service": "flows",
                "path": "/flows",
                "json": {
                    "flows": [
                        generate_hello_world_example_flow(i) for i in range(40, 60)
                    ],
                    "limit": 20,
                    "has_next_page": False,
                    "marker": None,
                },
                "match": [
                    matchers.query_param_matcher(
                        {"orderby": "updated_at DESC", "marker": "fake_marker_1"}
                    )
                ],
            },
        },
        metadata={
            "owner_id": OWNER_ID,
            "num_pages": 3,
            "expect_markers": ["fake_marker_0", "fake_marker_1", None],
            "total_items": 60,
        },
    )


# A list of usernames to assign to new pool identities.
_FLOWS_USERNAMES = (
    "pete@kreb.star",
    "nona@wellsville.gov",
    "artie@super.hero",
    "monica@kreb.scouts",
    "ellen@astro.camp",
    "larry@donkey.king",
    "louise@forest.zone",
    "simon@hover.board",
    "judy@cosmo.club",
    "manny@neon.city",
)
_FLOWS_SPECIAL_PRINCIPALS = ("public", "all_authenticated_users")


class FlowsIdentityPool:
    """
    A pool of identities for use in a particular flow test.

    The class is designed to be instantiated using the `load_identities_for_flow` and
    `load_identities_for_flow_run` fixtures.
    It accepts in a set of principal identities or URNs, assigning each a random unique
    username and exposing this data for fixture-responses patching as well
    as test verification (`get_username`).
    """

    def __init__(self, principals: set[str]) -> None:
        username_iter = iter(random.sample(_FLOWS_USERNAMES, k=len(principals)))

        # Mapping of identity-urn to username
        self._usernames = {
            principal: next(username_iter)
            for principal in principals
            if principal not in _FLOWS_SPECIAL_PRINCIPALS
        }

    def get_username(self, principal: str) -> str:
        """
        Return the username assigned to the given principal (or the principal itself it
        if it "public" or "all_authenticated_users").
        """
        if principal in _FLOWS_SPECIAL_PRINCIPALS:
            return principal
        return self._usernames[principal]

    def create_get_identities_documents(self) -> list[dict[str, str]]:
        """
        Render a partial identities document list for use in mocking Auth responses.
        """
        return [
            {"id": principal.split(":")[-1], "username": username}
            for principal, username in self._usernames.items()
        ]


@pytest.fixture
def load_identities_for_flow(get_identities_mocker):
    """
    Callable fixture.
    Load identities for a provided flow response object, configuring auth.get_identities
    to return unique usernames for each identity associated with the flow.

    Returns an identity pool object to facilitate lookup of username by principal urn.
    """

    flow_principal_keys = ("flow_administrators", "flow_starters", "flow_viewers")
    flow_run_principal_keys = ("run_managers", "run_monitors")

    def _load_identities_for_flow(flow: dict[str, t.Any]) -> FlowsIdentityPool:
        principals: set[str] = {flow.get("flow_owner")} or set()
        for key in flow_principal_keys + flow_run_principal_keys:
            principals.update(set(flow.get(key, [])))

        pool = FlowsIdentityPool(principals)

        get_identities_mocker.configure(pool.create_get_identities_documents())
        return pool

    return _load_identities_for_flow


@pytest.fixture
def load_identities_for_flow_run(get_identities_mocker):
    """
    Callable fixture.
    Load identities for a provided flow run response object, configuring
    auth.get_identities to return unique usernames for each identity associated with the
    flow.

    Returns an identity pool object to facilitate lookup of username by principal urn.
    """
    run_principal_keys = ("run_managers", "run_monitors")

    def _load_identities_for_run(flow_run: dict[str, t.Any]) -> FlowsIdentityPool:
        principals: set[str] = {flow_run.get("run_owner")} or set()
        for key in run_principal_keys:
            principals.update(set(flow_run.get(key, [])))

        pool = FlowsIdentityPool(principals)

        get_identities_mocker.configure(pool.create_get_identities_documents())
        return pool

    return _load_identities_for_run


@pytest.fixture(autouse=True, scope="session")
def setup_custom_orderby_response() -> None:
    register_response_set(
        "flows_list_orderby_title_asc",
        {
            "title_asc": {
                "service": "flows",
                "path": "/flows",
                "json": {
                    "flows": [
                        # chr(65) = 'A', so this is A-Z
                        generate_hello_world_example_flow(
                            i, title=f"{chr(65 + i)}-Sorted-Flow"
                        )
                        for i in range(26)
                    ],
                    "limit": 100,
                    "has_next_page": False,
                },
                "match": [matchers.query_param_matcher({"orderby": "title ASC"})],
            },
        },
        metadata={
            "owner_id": OWNER_ID,
            "total_items": 26,
        },
    )
