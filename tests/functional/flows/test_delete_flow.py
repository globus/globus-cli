import re

from globus_sdk._testing import RegisteredResponse, load_response


def test_delete_flow_text_output(run_line):
    delete_response = load_response("flows.delete_flow")
    flow_id = delete_response.metadata["flow_id"]
    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": [
                    {
                        "username": "legolas@rivendell.middleearth",
                        "name": "Orlando Bloom",
                        "id": delete_response.json["flow_owner"].split(":")[-1],
                        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
                        "organization": "Fellowship of the Ring",
                        "status": "used",
                        "email": "legolas@thewoodlandrealm.middleearth",
                    }
                ]
            },
        )
    )

    result = run_line(f"globus flows delete {flow_id}")
    # all fields present
    for fieldname in (
        "Deleted",
        "Flow ID",
        "Title",
        "Owner",
        "Created At",
        "Updated At",
    ):
        assert fieldname in result.output
    # owner was resolved to a username
    assert "legolas@rivendell.middleearth" in result.output
    # bool formatter worked as expected
    assert re.search(r"Deleted:\s+True", result.output) is not None
