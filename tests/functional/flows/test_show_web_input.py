from __future__ import annotations

import json
import re

from globus_sdk.testing import load_response


def test_show_web_input_text_output(run_line, load_identities_for_web_input):
    loaded_response = load_response("flows.get_web_input")
    response, meta = loaded_response.json, loaded_response.metadata

    web_input_id = meta["web_input_id"]

    pool = load_identities_for_web_input(response)

    result = run_line(f"globus flows web-input show {web_input_id}")

    # all fields present
    for fieldname in (
        "Web Input ID",
        "Status",
        "Input Type",
        "Title",
        "Your Roles",
        "Flow ID",
        "Flow Title",
        "Run ID",
        "Run Label",
        "Creator",
        "Viewers",
        "Respondents",
        "Created At",
        "Edited At",
        "Closed At",
    ):
        assert fieldname in result.output

    # Verify principal resolution.
    roles = response.get("roles", {})
    # "creator_urn" and "respondent_urns" are identity URNs, resolved to usernames.
    _assert_usernames(result, pool, "Creator", [response["creator_urn"]])
    _assert_usernames(result, pool, "Respondents", roles.get("respondent_urns", []))
    # "viewer_urns" is a group URN; expect an unresolved group ID.
    group_urn = roles["viewer_urns"][0]
    _, _, group_id = group_urn.rpartition(":")
    assert f"Globus Group ({group_id})" in _get_output_value("Viewers", result.output)

    # Expect 'text' content.
    assert "Context:" in result.output
    assert response["context"]["text"] in result.output

    # Options must be rendered so that users can quickly use the `respond` subcommand.
    assert "Options:" in result.output
    for option in response["options"]:
        assert option["option_id"] in result.output
        assert option["label"] in result.output


def test_show_web_input_table_context(run_line, load_identities_for_web_input):
    loaded_response = load_response("flows.get_web_input", case="table_context")
    response, meta = loaded_response.json, loaded_response.metadata

    web_input_id = meta["web_input_id"]
    load_identities_for_web_input(response)

    result = run_line(f"globus flows web-input show {web_input_id}")

    # Expect context rows to be rendered.
    assert "Context:" in result.output
    for row in response["context"]["rows"]:
        assert row["field"] in result.output
        assert row["value"] in result.output

    # Options must be rendered so that users can quickly use the `respond` subcommand.
    assert "Options:" in result.output
    for option in response["options"]:
        assert option["option_id"] in result.output
        assert option["label"] in result.output


def test_show_web_input_json_output(run_line, load_identities_for_web_input):
    loaded_response = load_response("flows.get_web_input")
    response, meta = loaded_response.json, loaded_response.metadata

    web_input_id = meta["web_input_id"]
    load_identities_for_web_input(response)

    result = run_line(f"globus flows web-input show {web_input_id} -F json")
    output = json.loads(result.output)
    assert output["id"] == meta["web_input_id"]


def _assert_usernames(result, pool, field_name, principals):
    expected_usernames = {pool.get_username(principal) for principal in principals}

    output_value = _get_output_value(field_name, result.output)
    output_usernames = {x.strip() for x in output_value.split(",")}
    assert expected_usernames == output_usernames


def _get_output_value(name, output):
    """
    Return the value for a specified field from the output of a command.
    """
    match = re.search(
        rf"^{re.escape(name)}:[^\S\n\r]+(?P<value>.*)$", output, flags=re.M
    )
    assert match is not None
    return match.group("value")
