import uuid

import pytest
from globus_sdk.scopes import SpecificFlowScopes
from globus_sdk.testing import RegisteredResponse


@pytest.mark.parametrize(
    "method,path,command",
    (
        # delete-flow
        ("DELETE", "/flows/{flow_id}", "globus flows delete {flow_id}"),
        # run-flow
        ("POST", "/flows/{flow_id}/run", "globus flows start {flow_id}"),
        # get-flow
        ("GET", "/flows/{flow_id}", "globus flows show {flow_id}"),
        # update-flow
        ("PUT", "/flows/{flow_id}", "globus flows update {flow_id}"),
    ),
)
def test_flow_route_gare_handling(run_line, add_flow_login, method, path, command):
    """
    Ensure that every specific flow command (one that accepts a flow id argument)
    suggests a resolution for GAREs which propagates to specific-flow tokens.
    """
    policy_id = str(uuid.uuid4())
    flow_id = str(uuid.uuid4())
    flow_scope = SpecificFlowScopes(flow_id).user

    add_flow_login(flow_id)
    path = path.format(flow_id=flow_id)
    command = command.format(flow_id=flow_id)

    _load_flows_gare(method, path, policy_id)

    result = run_line(command, assert_exit_code=4)

    login_cmd = f"globus session update --policy '{policy_id}' --scope '{flow_scope}'"
    assert login_cmd in result.stdout


@pytest.mark.parametrize(
    "method,path,command",
    (
        # delete-run
        ("POST", "/runs/{run_id}/release", "globus flows run delete {run_id}"),
        # cancel-run
        ("POST", "/runs/{run_id}/cancel", "globus flows run cancel {run_id}"),
        # update-run
        ("PUT", "/runs/{run_id}", "globus flows run update {run_id}"),
        # resume-run
        # Note: this command  calls get-run first, so we patch that instead.
        ("GET", "/runs/{run_id}", "globus flows run resume {run_id}"),
        # show-run
        ("GET", "/runs/{run_id}", "globus flows run show {run_id}"),
        # show-run-definition
        (
            "GET",
            "/runs/{run_id}/definition",
            "globus flows run show-definition {run_id}",
        ),
        # show-run-logs
        ("GET", "/runs/{run_id}/log", "globus flows run show-logs {run_id}"),
    ),
)
def test_run_route_gare_handling(run_line, add_flow_login, method, path, command):
    """
    Ensure that every specific run command (one that accepts a run id argument)
    suggests a resolution for GAREs which propagates to specific-flow tokens.
    """
    policy_id = str(uuid.uuid4())
    flow_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    flow_scope = SpecificFlowScopes(flow_id).user

    add_flow_login(flow_id)
    path = path.format(flow_id=flow_id, run_id=run_id)
    command = command.format(flow_id=flow_id, run_id=run_id)

    _load_flows_gare(method, path, policy_id)
    _load_run_meta_in_search_query(run_id, flow_id)

    result = run_line(command, assert_exit_code=4)
    login_cmd = f"globus session update --policy '{policy_id}' --scope '{flow_scope}'"
    assert login_cmd in result.stdout


def test_run_route_gare_handling_when_flow_not_in_search(run_line, add_flow_login):
    """
    Ensure that when a run command is invoked and the run's flow is not found in search,
    the GARE is re-raised unmodified (i.e. no flow scope injection attempted).
    """

    policy_id = str(uuid.uuid4())
    flow_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    add_flow_login(flow_id)

    _load_flows_gare("GET", f"/runs/{run_id}", policy_id)

    result = run_line(
        f"globus flows run show {run_id}",
        assert_exit_code=4,
    )

    assert flow_id not in result.stdout
    assert f"globus session update --policy '{policy_id}'" in result.stdout


def _load_flows_gare(method: str, path: str, policy_id: str) -> RegisteredResponse:
    """
    Load a GARE response for the flows service with the specified method/path
    and session policy ID.
    """
    return RegisteredResponse(
        service="flows",
        method=method,
        path=path,
        status=403,
        json={
            "code": "AuthenticationPolicyRequired",
            "authorization_parameters": {
                "session_message": (
                    "Globus Flows detected an unsatisfied session policy for this "
                    "resource."
                ),
                "session_required_policies": [policy_id],
            },
            "debug_id": str(uuid.uuid4()),
        },
    ).add()


def _load_run_meta_in_search_query(run_id: str, flow_id: str) -> RegisteredResponse:
    """Load a search response which returns the specified flow_id for the run_id."""
    return RegisteredResponse(
        service="search",
        method="POST",
        path="v1/index/2a318659-a547-4b48-a0fc-e0c19081a960/search",
        status=200,
        json={
            "total": 1,
            "gmeta": [
                {
                    "@datatype": "GMetaResult",
                    "@version": "2019-08-27",
                    "subject": f"runs/{run_id}",
                    "entries": [
                        {
                            "content": {
                                "run_id": run_id,
                                "flow_id": flow_id,
                            },
                            "matched_principal_sets": ["owner", "flow_run_managers"],
                        }
                    ],
                }
            ],
            "@datatype": "GSearchResult",
            "@version": "2017-09-01",
            "offset": 0,
            "count": 1,
            "has_next_page": False,
        },
    ).add()
