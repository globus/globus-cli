import re
import uuid

from globus_sdk.testing import RegisteredResponse, load_response


def test_update_run_text_output(run_line, add_flow_login, get_identities_mocker):
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
    }
    run_manager_identities = [
        {
            "username": "booboo@jellystone.park",
            "name": "Boo Boo",
            "id": run_managers[0].split(":")[-1],
        },
    ]
    run_monitor_identities = [
        {
            "username": "snaggle@jellystone.park",
            "name": "Snagglepuss",
            "id": run_monitors[0].split(":")[-1],
        },
        {
            "username": "yakky@jellystone.park",
            "name": "Yakky Doodle",
            "id": run_monitors[1].split(":")[-1],
        },
    ]
    get_identities_mocker.configure(
        [owner_identity, *run_manager_identities, *run_monitor_identities]
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


# this is a regression test for an error shape seen in production
# in which run update is missing `$.error.message`
def test_handling_for_run_update_error(run_line):
    run_id = str(uuid.uuid1())
    RegisteredResponse(
        service="flows",
        path=f"/runs/{run_id}",
        method="PUT",
        json={
            "error": {
                "code": "UNPROCESSABLE_ENTITY",
                "detail": [
                    {
                        "loc": ["label"],
                        "msg": "ensure this value has at most 64 characters",
                        "type": "value_error.any_str.max_length",
                        "ctx": {"limit_value": 64},
                    }
                ],
            },
            "debug_id": "094a222b-2819-4129-9979-7f51f57cd7d9",
        },
        status=422,
    ).add()
    result = run_line(
        ["globus", "flows", "run", "update", run_id, "--label", "a" * 80],
        assert_exit_code=1,
    )
    assert "$.label: ensure this value has at most 64 characters" in result.stderr
