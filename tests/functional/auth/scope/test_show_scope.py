from __future__ import annotations

import json
import textwrap

import pytest
from globus_sdk._testing import load_response_set


@pytest.mark.parametrize(
    "scope_id_or_string",
    (
        "24f3dcbe-7655-4721-bc64-d1c5d635b9a1",
        "https://auth.globus.org/scopes/actions.globus.org/hello_world",
    ),
)
def test_show_scope(run_line, scope_id_or_string):
    load_response_set("cli.scopes")

    result = run_line(f"globus auth scope show {scope_id_or_string}")

    expected_output = textwrap.dedent(
        """
        Scope String:          https://auth.globus.org/scopes/actions.globus.org/hello_world
        Scope ID:              24f3dcbe-7655-4721-bc64-d1c5d635b9a1
        Name:                  Hello World Action
        Description:           Allow the Hello World action to extend greetings.
        Client ID:             5fac2e64-c734-4e6b-90ea-ff12ddbf9653
        Allows Refresh Tokens: True
        Required Domains:      []
        Advertised:            True
        Dependent Scopes:
          - Scope String:           urn:globus:auth:scope:nexus.api.globus.org:groups
            Scope ID:               69a73d8f-cd45-4e37-bb3b-43678424aeb7
            Optional:               False
            Requires Refresh Token: False
          - Scope String:           urn:globus:auth:scope:groups.api.globus.org:view_my_groups_and_memberships
            Scope ID:               73320ffe-4cb4-4b25-a0a3-83d53d59ce4f
            Optional:               False
            Requires Refresh Token: False
        """  # noqa: E501
    ).strip()

    # Remove trailing spaces from the command output.
    stdout = "\n".join(line.rstrip() for line in result.stdout.splitlines())

    assert stdout == expected_output


def test_show_scope_json_omits_dependent_scope_string(run_line):
    meta = load_response_set("cli.scopes").metadata
    scope_id = meta["hello_world_id"]

    result = run_line(f"globus auth scope show {scope_id} -F json")

    loaded = json.loads(result.stdout)
    assert loaded["scope"]["dependent_scopes"][0].get("scope_string") is None
