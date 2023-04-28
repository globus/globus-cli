import json
import re

from globus_sdk._testing import RegisteredResponse, load_response


def test_start_flow_text_output(run_line, add_flow_login):
    # Load the response mock and extract critical metadata.
    response = load_response("flows.run_flow")
    flow_id = response.metadata["flow_id"]
    body = response.metadata["request_params"]["body"]
    tags = response.metadata["request_params"]["tags"]
    label = response.metadata["request_params"]["label"]
    run_monitors = response.metadata["request_params"]["run_monitors"]
    run_managers = response.metadata["request_params"]["run_managers"]
    add_flow_login(flow_id)

    # Configure identities.
    owner_identity = {
        "username": "yogi@jellystone.park",
        "name": "Yogi",
        "id": response.json["run_owner"].split(":")[-1],
        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
        "organization": "Hanna-Barbera",
        "status": "used",
        "email": "yogi@jellystone.park",
    }
    run_manager_identities = [
        {
            "username": "booboo@jellystone.park",
            "name": "Boo Boo",
            "id": run_managers[0].split(":")[-1],
            "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
            "organization": "Hanna-Barbera",
            "status": "used",
            "email": "booboo@jellystone.park",
        },
    ]
    run_monitor_identities = [
        {
            "username": "snaggle@jellystone.park",
            "name": "Snagglepuss",
            "id": run_monitors[0].split(":")[-1],
            "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
            "organization": "Hanna-Barbera",
            "status": "used",
            "email": "snagglepuss@jellystone.park",
        },
        {
            "username": "yakky@jellystone.park",
            "name": "Yakky Doodle",
            "id": run_monitors[1].split(":")[-1],
            "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
            "organization": "Hanna-Barbera",
            "status": "used",
            "email": "yakky@jellystone.park",
        },
    ]
    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": [
                    owner_identity,
                    *run_manager_identities,
                    *run_monitor_identities,
                ],
            },
        )
    )

    # Construct the command line.
    arguments = [f"'{flow_id}'", "--input", f"'{json.dumps(body)}'"]
    for run_manager in run_managers:
        arguments.extend(("--manager", f"'{run_manager}'"))
    for run_monitor in run_monitors:
        arguments.extend(("--monitor", f"'{run_monitor}'"))
    for tag in tags:
        arguments.extend(("--tag", f"'{tag}'"))
    if label is not None:
        arguments.extend(("--label", f"'{label}'"))

    result = run_line(f"globus flows start {' '.join(arguments)}")

    # all fields present
    expected_fields = {
        "Flow ID",
        "Flow title",
        "Run ID",
        "Run label",
        "Run owner",
        "Run managers",
        "Run monitors",
        "Run tags",
    }
    actual_fields = set(re.findall(r"^[\w ]+(?=:)", result.output, flags=re.M))
    assert expected_fields == actual_fields, "Expected and actual field sets differ"

    tag_match = re.search(r"^Run tags:\s+(?P<tags>.+)$", result.output, flags=re.M)
    assert tag_match is not None
    assert ", ".join(tags) in tag_match.group("tags")

    owner_match = re.search(r"^Run owner:\s+(?P<owner>.+)$", result.output, flags=re.M)
    assert owner_match is not None
    assert owner_match.group("owner") == owner_identity["username"]

    managers_match = re.search(
        r"^Run managers:\s+(?P<managers>.+)$", result.output, flags=re.M
    )
    assert managers_match is not None
    assert managers_match.group("managers") == ", ".join(
        identity["username"] for identity in run_manager_identities
    )

    monitors_match = re.search(
        r"^Run monitors:\s+(?P<monitors>.+)$", result.output, flags=re.M
    )
    assert monitors_match is not None
    assert monitors_match.group("monitors") == ", ".join(
        identity["username"] for identity in run_monitor_identities
    )


def test_start_flow_rejects_non_object_input(run_line, add_flow_login):
    # setup test requirements for success to ensure that the test won't be sensitive to
    # the order in which checks which happen
    # (e.g. login check happening before the input shape check)
    response = load_response("flows.run_flow")
    flow_id = response.metadata["flow_id"]
    add_flow_login(flow_id)

    result = run_line(
        ["globus", "flows", "start", flow_id, "--input", json.dumps(["foo", "bar"])],
        assert_exit_code=2,
    )
    assert "Flow input cannot be non-object JSON data" in result.stderr
