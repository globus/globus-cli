import re

from globus_sdk._testing import RegisteredResponse, load_response


def test_show_flow_text_output(run_line):
    get_response = load_response("flows.get_flow")
    flow_id = get_response.metadata["flow_id"]
    keywords = get_response.json["keywords"]
    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": [
                    {
                        "username": "legolas@rivendell.middleearth",
                        "name": "Orlando Bloom",
                        "id": get_response.json["flow_owner"].split(":")[-1],
                        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
                        "organization": "Fellowship of the Ring",
                        "status": "used",
                        "email": "legolas@thewoodlandrealm.middleearth",
                    }
                ]
            },
        )
    )

    result = run_line(f"globus flows show {flow_id}")
    # all fields present
    for fieldname in (
        "Flow ID",
        "Title",
        "Keywords",
        "Owner",
        "Created At",
        "Updated At",
        "Administrators",
        "Viewers",
        "Starters",
    ):
        assert fieldname in result.output
    # array formatters worked as expected
    assert (
        re.search(r"Keywords:\s+" + re.escape(",".join(keywords)), result.output)
        is not None
    )
    assert (
        re.search(r"Administrators:\s+legolas@rivendell\.middleearth", result.output)
        is not None
    )
    assert (
        re.search(r"Viewers:\s+public,legolas@rivendell\.middleearth", result.output)
        is not None
    )
    assert (
        re.search(
            r"Starters:\s+all_authenticated_users,legolas@rivendell\.middleearth",
            result.output,
        )
        is not None
    )
