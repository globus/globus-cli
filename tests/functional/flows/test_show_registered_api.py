from __future__ import annotations

import re

from globus_sdk.testing import load_response


def test_show_registered_api_text_output(run_line, load_identities_for_registered_api):
    loaded_response = load_response("flows.get_registered_api")
    response, meta = loaded_response.json, loaded_response.metadata

    registered_api_id = meta["registered_api_id"]

    pool = load_identities_for_registered_api(response)

    result = run_line(f"globus flows registered-api show {registered_api_id}")

    # all fields present
    for fieldname in (
        "Registered API ID",
        "Name",
        "Description",
        "Status",
        "Subscription ID",
        "Created At",
        "Updated At",
        "Owners",
        "Administrators",
        "Viewers",
        "Target Type",
        "OpenAPI Version",
        "Destination Method",
        "Destination URL",
    ):
        assert fieldname in result.output

    # Verify principal resolution
    roles = response.get("roles", {})
    assert_usernames(result, pool, "Owners", roles.get("owners", []))
    assert_usernames(result, pool, "Administrators", roles.get("administrators", []))
    assert_usernames(result, pool, "Viewers", roles.get("viewers", []))


def assert_usernames(result, pool, field_name, principals):
    expected_usernames = {pool.get_username(principal) for principal in principals}

    output_value = _get_output_value(field_name, result.output)
    output_usernames = [x.strip() for x in output_value.split(",")]
    assert expected_usernames == set(output_usernames)


def _get_output_value(name, output):
    """
    Return the value for a specified field from the output of a command.
    """
    match = re.search(rf"^{name}:[^\S\n\r]+(?P<value>.*)$", output, flags=re.M)
    assert match is not None
    return match.group("value")
