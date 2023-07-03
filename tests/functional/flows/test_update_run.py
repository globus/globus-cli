import re

from globus_sdk._testing import RegisteredResponse, load_response


def test_update_run_text_output(run_line, add_flow_login):
    # Load the response mock and extract critical metadata.
    response = load_response("flows.update_run")
    flow_id = response.metadata["flow_id"]
    run_id = response.metadata["run_id"]
    tags = response.json["tags"]
    label = response.json["label"]
    run_monitors = response.json["run_monitors"]
    run_managers = response.json["run_managers"]
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
    arguments = [
        f"'{run_id}'",
        "--label",
        f"'{label}'",
        "--monitors",
        f"'{','.join(run_monitors)}'",
        "--managers",
        f"'{','.join(run_managers)}'",
        "--tags",
        f"'{','.join(tags)}'",
    ]

    result = run_line(f"globus flows run update {' '.join(arguments)}")

    # Verify all fields are present.
    expected_fields = {
        "Flow ID",
        "Flow Title",
        "Run ID",
        "Run Label",
        "Run Managers",
        "Run Monitors",
        "Run Tags",
    }
    for field in expected_fields:
        assert field in result.output, f"'{field}' is not present in the output"

    tag_match = re.search(r"^Run Tags:\s+(?P<tags>.+)$", result.output, flags=re.M)
    assert tag_match is not None
    assert ", ".join(tags) in tag_match.group("tags")

    managers_match = re.search(
        r"^Run Managers:\s+(?P<managers>.+)$", result.output, flags=re.M
    )
    assert managers_match is not None
    assert managers_match.group("managers") == ", ".join(
        identity["username"] for identity in run_manager_identities
    )

    monitors_match = re.search(
        r"^Run Monitors:\s+(?P<monitors>.+)$", result.output, flags=re.M
    )
    assert monitors_match is not None
    assert monitors_match.group("monitors") == ", ".join(
        identity["username"] for identity in run_monitor_identities
    )
