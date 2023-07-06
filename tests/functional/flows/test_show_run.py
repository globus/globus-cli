import re

import pytest
import responses
from globus_sdk._testing import RegisteredResponse, load_response


@pytest.mark.parametrize("include_flow_description", (True, False))
def test_show_run_text_output(run_line, add_flow_login, include_flow_description):
    # Load the response mock and extract critical metadata.
    response = load_response("flows.get_run")
    run_id = response.metadata["run_id"]
    tags = response.responses[0].json["tags"]
    label = response.responses[0].json["label"]
    run_owner = response.responses[0].json["run_owner"]
    run_manager = response.responses[0].json["run_managers"][0]
    run_monitor = response.responses[0].json["run_monitors"][0]

    # Configure identities.
    run_owner_identity = {
        "username": "gabe_walker@mountainrescue.biz",
        "id": run_owner.split(":")[-1],
    }
    run_manager_identity = {
        "username": "hal_tucker@mountainrescue.biz",
        "id": run_manager.split(":")[-1],
    }
    run_monitor_identity = {
        "username": "team@mountainrescue.biz",  # Globus Group
        "id": run_monitor.split(":")[-1],
    }
    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": [
                    run_owner_identity,
                    run_manager_identity,
                    run_monitor_identity,
                ]
            },
        )
    )

    # Construct the command line.
    cli = f"globus flows run show {run_id}"
    if include_flow_description:
        cli += " --include-flow-description"
    result = run_line(cli)

    # Verify query parameters are only conditionally included.
    request = responses.calls[0].request
    if include_flow_description:
        assert "?include_flow_description=true" in request.url.lower()
    else:
        assert "include_flow_description" not in request.url.lower()

    # Verify all fields are present.
    expected_fields = {
        "Flow ID",
        "Flow Title",
        "Run ID",
        "Run Label",
        "Run Owner",
        "Run Managers",
        "Run Monitors",
        "Run Tags",
        "Started At",
        "Completed At",
        "Status",
    }
    for field in expected_fields:
        assert field in result.output, f"'{field}' is not present in the output"

    # Several fields are optional. Verify that they are -- or are not -- present.
    for field in {"Flow Subtitle", "Flow Description", "Flow Keywords"}:
        if include_flow_description:
            assert field in result.output, f"'{field}' is not present in the output"
        else:  # The field should *not* be present
            assert field not in result.output, f"'{field}' is present in the output"

    label_match = re.search(r"^Run Label:\s+(?P<label>.+)$", result.output, flags=re.M)
    assert label_match is not None
    assert label_match.group("label") == label

    tag_match = re.search(r"^Run Tags:\s+(?P<tags>.+)$", result.output, flags=re.M)
    assert tag_match is not None
    assert ", ".join(tags) in tag_match.group("tags")

    owner_match = re.search(r"^Run Owner:\s+(?P<owner>.+)$", result.output, flags=re.M)
    assert owner_match is not None
    assert owner_match.group("owner") == run_owner_identity["username"]

    managers_match = re.search(
        r"^Run Managers:\s+(?P<managers>.+)$", result.output, flags=re.M
    )
    assert managers_match is not None
    assert managers_match.group("managers") == run_manager_identity["username"]

    monitors_match = re.search(
        r"^Run Monitors:\s+(?P<monitors>.+)$", result.output, flags=re.M
    )
    assert monitors_match is not None
    expected = f'Globus Group ({run_monitor_identity["id"]})'
    assert monitors_match.group("monitors") == expected
