import json
import re
import uuid
from itertools import chain
from random import shuffle

import pytest
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


class IdentityPool:
    IDENTITY_DATA = FLOW_IDENTITIES

    def __init__(self):
        self.identities = {}
        self.assigned_sets = {}

    def assign(self, set_name, principal_set):
        """
        Assign a list of identities for the provided principal set, updating the
        stored identities dict with any new identities that are created so they can
        be reused.

        set_name is the name of the key to store the assigned identities under
        principal_set is a list of principals in the request
        """
        self.assigned_sets[set_name] = identity_set = []
        # Randomize the names for each principal set
        available_identities = list(self.IDENTITY_DATA.keys())
        shuffle(available_identities)

        # Iterate over the principals in the request
        for index, principal in enumerate(principal_set):
            if principal in self.identities:
                # Use the existing identity if it's already been assigned
                identity_set.append(self.identities[principal])
                continue

            if principal not in SPECIAL_PRINCIPALS:
                # Attempt to assign distinct identities to each principal
                identity = self.create_identity(
                    principal.split(":")[-1],
                    available_identities[index % len(available_identities)],
                )
                identity_set.append(identity)
                self.identities[principal] = identity

        return identity_set

    def get_assigned_usernames(self, set_name):
        """
        Return a list of usernames for the provided set_name.
        """
        return [identity["username"] for identity in self.assigned_sets[set_name]]

    @classmethod
    def create_identity(cls, id, name):
        """
        Return an identity dict using the provided id for the user corresponding
        to the provided name.
        """
        identity = cls.IDENTITY_DATA[name].copy()
        identity["id"] = id
        return identity


def value_for_field_from_output(name, output):
    """
    Return the value for a specified field from the output of a command.
    """
    match = re.search(rf"^{name}:[^\S\n\r]+(?P<value>.*)$", output, flags=re.M)
    assert match is not None
    return match.group("value")


def test_update_flow_text_output(run_line):
    # Load the response mock and extract metadata
    response = load_response("flows.update_flow")
    flow_id = response.metadata["flow_id"]
    definition = response.json["definition"]
    input_schema = response.json["input_schema"]
    keywords = response.json["keywords"]
    title = response.json["title"]
    subtitle = response.json["subtitle"]
    description = response.json["description"]
    flow_owner = response.json["flow_owner"]
    flow_administrators = response.json["flow_administrators"]
    flow_starters = response.json["flow_starters"]
    flow_viewers = response.json["flow_viewers"]

    pool = IdentityPool()

    # Configure the identities for all roles
    pool.assign("owner", [flow_owner])
    pool.assign("administrators", flow_administrators)
    pool.assign("starters", flow_starters)
    pool.assign("viewers", flow_viewers)

    load_response(
        RegisteredResponse(
            service="auth",
            path="/v2/api/identities",
            json={
                "identities": list(pool.identities.values()),
            },
        )
    )

    # Construct the command line
    options = [
        ("--definition", json.dumps(definition)),
        ("--input-schema", json.dumps(input_schema)),
        ("--title", title),
        ("--subtitle", subtitle),
        ("--description", description),
        ("--owner", flow_owner),
    ]
    for flow_administrator in flow_administrators:
        options.append(("--administrator", flow_administrator))
    for flow_starter in flow_starters:
        options.append(("--starter", flow_starter))
    for flow_viewer in flow_viewers:
        options.append(("--viewer", flow_viewer))
    for keyword in keywords:
        options.append(("--keyword", keyword))

    command = ["globus", "flows", "update", flow_id, *chain.from_iterable(options)]

    result = run_line(command)

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
        "Owner": pool.get_assigned_usernames("owner")[0],
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
            *pool.get_assigned_usernames("administrators"),
        },
        "Starters": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_starters
            ],
            *pool.get_assigned_usernames("starters"),
        },
        "Viewers": {
            *[
                principal
                for principal in SPECIAL_PRINCIPALS
                if principal in flow_viewers
            ],
            *pool.get_assigned_usernames("viewers"),
        },
    }

    for name, expected_values in expected_sets.items():
        match_list = set(value_for_field_from_output(name, result.output).split(","))
        assert match_list == expected_values


@pytest.mark.parametrize("thing", ["administrator", "starter", "viewer", "keyword"])
def test_mutually_exclusive_options(thing, run_line):
    """Ensure that mutex options cause failures."""

    command = f"globus flows update {uuid.uuid4()} --{thing} value --no-{thing}s"
    run_line(command, assert_exit_code=2, matcher="are mutually exclusive")


@pytest.mark.parametrize("option", ["definition", "input-schema"])
def test_json_object_option_validation(option, run_line):
    """Ensure options that must be JSON objects are validated as such."""

    command = f"globus flows update {uuid.uuid4()} --{option} '[]'"
    run_line(command, assert_exit_code=2, matcher="must be a JSON object")
