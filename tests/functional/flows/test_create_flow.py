import json
import re
from random import shuffle

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

SPECIAL_PRINCIPALS = ["public", "all_authenticated_users"]


def get_identity(id, name):
    """
    Return an identity dict using the provided id for the user corresponding
    to the provided name.
    """
    identity = FLOW_IDENTITIES[name].copy()
    identity["id"] = id
    return identity


def assign_identities_for_principal_set(principal_set, existing_identities):
    """
    Return a list of identities for the provided principal set, updating the provided
    existing_identities dict with any new identities that are created.

    principal_set is a list of principals in the request
    existing_identities is a dict mapping principal URNs to identities
    """
    identity_set = []
    # Randomize the names for each principal set
    available_identities = list(FLOW_IDENTITIES.keys())
    shuffle(available_identities)

    # Iterate over the principals in the request
    for index, principal in enumerate(principal_set):
        if principal in existing_identities:
            # Use the existing identity if it's already been assigned
            identity_set.append(existing_identities[principal])
            continue

        if principal not in SPECIAL_PRINCIPALS:
            # Attempt to assign distinct identities to each principal
            identity = get_identity(
                principal.split(":")[-1],
                available_identities[index % len(available_identities)],
            )
            identity_set.append(identity)
            existing_identities[principal] = identity

    return identity_set


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

    # Configure the owner identity
    owner_identity = get_identity(response.json["flow_owner"].split(":")[-1], "pete")
    identities = {response.json["flow_owner"]: owner_identity}

    # Configure the identities for other roles
    flow_administrator_identities = assign_identities_for_principal_set(
        principal_set=flow_administrators,
        existing_identities=identities,
    )
    flow_starter_identities = assign_identities_for_principal_set(
        principal_set=flow_starters,
        existing_identities=identities,
    )
    flow_viewer_identities = assign_identities_for_principal_set(
        principal_set=flow_viewers,
        existing_identities=identities,
    )

    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": list(identities.values()),
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
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_administrators
            ],
            *[identity["username"] for identity in flow_administrator_identities],
        },
        "Starters": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_starters
            ],
            *[identity["username"] for identity in flow_starter_identities],
        },
        "Viewers": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_viewers
            ],
            *[identity["username"] for identity in flow_viewer_identities],
        },
    }

    for name, expected_values in expected_sets.items():
        match_list = set(value_for_field_from_output(name, result.output).split(","))
        assert match_list == expected_values
