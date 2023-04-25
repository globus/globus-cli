import json
import re

from globus_sdk._testing import RegisteredResponse, load_response

FLOW_IDENTITIES = {
    "pete": {
        "username": "pete@kreb.star",
        "name": "Pete Wrigley",
        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
        "organization": "KrebStar Corp",
        "status": "used",
        "email": "pete@kreb.star",
    },
    "nona": {
        "username": "nona@wellsville.gov",
        "name": "Nona F. Mecklenberg",
        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
        "organization": "The City of Wellsville",
        "status": "used",
        "email": "nona@wellsville.gov",
    },
    "artie": {
        "username": "artie@super.hero",
        "name": "The Strongest Man in the World",
        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
        "organization": "Personal Superheroes",
        "status": "used",
        "email": "artie@super.hero",
    },
    "monica": {
        "username": "monica@kreb.scouts",
        "name": "Monica Perling",
        "identity_provider": "c8abac57-560c-46c8-b386-f116ed8793d5",
        "organization": "Kreb Scouts",
        "status": "used",
        "email": "monica@kreb.scouts",
    },
}


def get_identity(id, name):
    """
    Return an identity dict using the provided id for the user corresponding
    to the provided name.
    """
    identity = FLOW_IDENTITIES[name].copy()
    identity["id"] = id
    return identity


def value_for_field_from_output(name, output):
    """
    Return the value for a specified field from the output of a command.
    """
    match = re.search(rf"^{name}:[^\S\n\r]+(?P<value>.*)$", output, flags=re.M)
    assert match is not None
    return match.group("value")


def test_create_flow_text_output(run_line):
    # Load the response mock and extract metadata
    response = load_response("flows.create_flow")
    definition = response.metadata["params"]["definition"]
    input_schema = response.metadata["params"]["input_schema"]
    keywords = response.metadata["params"]["keywords"]
    title = response.metadata["params"]["title"]
    subtitle = response.metadata["params"]["subtitle"]
    description = response.metadata["params"]["description"]
    flow_administrators = response.metadata["params"]["flow_administrators"]
    flow_starters = response.metadata["params"]["flow_starters"]
    flow_viewers = response.metadata["params"]["flow_viewers"]

    # Configure identities
    owner_identity = get_identity(response.json["flow_owner"].split(":")[-1], "pete")
    flow_administrator_identities = [
        get_identity(flow_administrators[0].split(":")[-1], "nona")
    ]
    flow_starter_identities = [get_identity(flow_starters[0].split(":")[-1], "artie")]
    flow_viewer_identities = [get_identity(flow_viewers[0].split(":")[-1], "monica")]

    # FIXME: Remove as soon as upstream SDK changes are released
    flow_administrator_identities = [owner_identity]
    flow_starter_identities = [owner_identity]
    flow_viewer_identities = [owner_identity]

    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": [
                    owner_identity,
                    *flow_administrator_identities,
                    *flow_starter_identities,
                    *flow_viewer_identities,
                ],
            },
        )
    )

    # Construct the command line
    arguments = [
        f"'{title}'",
        f"'{json.dumps(definition)}'",
    ]
    for flow_administrator in flow_administrators:
        arguments.extend(("--administrator", f"'{flow_administrator}'"))
    for flow_starter in flow_starters:
        arguments.extend(("--starter", f"'{flow_starter}'"))
    for flow_viewer in flow_viewers:
        arguments.extend(("--viewer", f"'{flow_viewer}'"))
    for keyword in keywords:
        arguments.extend(("--keyword", f"'{keyword}'"))
    if input_schema is not None:
        arguments.extend(("--input-schema", f"'{json.dumps(input_schema)}'"))
    if subtitle is not None:
        arguments.extend(("--subtitle", f"'{subtitle}'"))
    if description is not None:
        arguments.extend(("--description", f"'{description}'"))

    result = run_line(f"globus flows create {' '.join(arguments)}")

    # Check all fields are present
    expected_fields = {
        "Flow ID",
        "Title",
        "Subtitle",
        "Description",
        "Keywords",
        "Owner",
        "Created At",
        "Updated At",
        "Administrators",
        "Starters",
        "Viewers",
    }
    actual_fields = set(re.findall(r"^[\w ]+(?=:)", result.output, flags=re.M))
    assert expected_fields == actual_fields, "Expected and actual field sets differ"

    # Check values for simple fields
    simple_fields = {
        "Owner": owner_identity["username"],
        "Title": title or "",
        "Subtitle": subtitle or "",
        "Description": description or "",
    }

    for name, value in simple_fields.items():
        assert value_for_field_from_output(name, result.output) == value

    # Check all multi-value fields
    expected_sets = {
        "Keywords": set(keywords),
        "Administrators": {
            *[identity["username"] for identity in flow_administrator_identities]
        },
        "Starters": {
            "all_authenticated_users",
            *[identity["username"] for identity in flow_starter_identities],
        },
        "Viewers": {
            "public",
            *[identity["username"] for identity in flow_viewer_identities],
        },
    }

    for name, expected_values in expected_sets.items():
        match_list = set(value_for_field_from_output(name, result.output).split(","))
        assert match_list == expected_values
