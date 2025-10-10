import json
import uuid

import pytest
import responses
from globus_sdk.testing import load_response_set


@pytest.mark.parametrize("ep_type", ["personal", "share", "server"])
def test_endpoint_set_subscription_id(run_line, ep_type):
    meta = load_response_set("cli.endpoint_operations").metadata
    if ep_type == "personal":
        epid = meta["gcp_endpoint_id"]
    elif ep_type == "share":
        epid = meta["share_id"]
    else:
        epid = meta["endpoint_id"]
    subscription_id = str(uuid.UUID(int=0))
    run_line(f"globus endpoint set-subscription-id {epid} {subscription_id}")
    assert (
        json.loads(responses.calls[-1].request.body)["subscription_id"]
        == subscription_id
    )


def test_endpoint_set_subscription_id_null(run_line):
    meta = load_response_set("cli.endpoint_operations").metadata
    epid = meta["gcp_endpoint_id"]
    subscription_id = "null"
    run_line(f"globus endpoint set-subscription-id {epid} {subscription_id}")
    assert json.loads(responses.calls[-1].request.body)["subscription_id"] is None


def test_endpoint_set_subscription_id_invalid_subscription_id(run_line):
    endpoint_id = str(uuid.UUID(int=0))
    subscription_id = "invalid-uuid"
    run_line(
        f"globus endpoint set-subscription-id {endpoint_id} {subscription_id}",
        assert_exit_code=2,
        search_stderr="Invalid value for 'SUBSCRIPTION_ID'",
    )
