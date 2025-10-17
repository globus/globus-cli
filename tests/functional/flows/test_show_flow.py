from __future__ import annotations

import re

from globus_sdk.testing import load_response


def test_show_flow_text_output(run_line, load_identities_for_flow):
    loaded_response = load_response("flows.get_flow")
    response, meta = loaded_response.json, loaded_response.metadata

    flow_id = meta["flow_id"]
    keywords = response["keywords"]

    pool = load_identities_for_flow(response)

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
        "Run Managers",
        "Run Monitors",
    ):
        assert fieldname in result.output

    assert _get_output_value("Keywords", result.output) == ", ".join(keywords)

    assert_usernames(result, pool, "Owner", [response["flow_owner"]])
    assert_usernames(result, pool, "Viewers", response["flow_viewers"])
    assert_usernames(result, pool, "Administrators", response["flow_administrators"])
    assert_usernames(result, pool, "Starters", response["flow_starters"])
    assert_usernames(result, pool, "Run Managers", response["run_managers"])
    assert_usernames(result, pool, "Run Monitors", response["run_monitors"])


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
