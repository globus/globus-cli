import contextlib
import json
import sys

import click
import pytest

from globus_cli.commands.flows.start import ActivityNotificationPolicyType
from globus_cli.parsing import ParsedJSONData


@click.command()
@click.option("-o", type=ActivityNotificationPolicyType())
def simple_command(o):
    if o is None:
        click.echo("nil")
    else:
        assert isinstance(o, ParsedJSONData)
        click.echo(f"filename: {o.filename or 'null'}")
        click.echo(f"data: {json.dumps(o.data, sort_keys=True)}")


def test_activity_notification_policy_metavar_rendering(runner):
    # in helptext, it shows up with the correct metavar
    result = runner.invoke(simple_command, ["--help"])
    assert "-o [{INACTIVE,FAILED,SUCCEEDED}|JSON_FILE|JSON]" in result.output


@pytest.mark.parametrize(
    "input_str,parsed_as",
    (
        # typical cases, including repetition and mixed case
        ("INACTIVE", ["INACTIVE"]),
        ("INACTIVE,INACTIVE", ["INACTIVE", "INACTIVE"]),
        ("inactive,succeeded", ["INACTIVE", "SUCCEEDED"]),
        (
            "FAILED,inactive,Failed,Succeeded",
            ["FAILED", "INACTIVE", "FAILED", "SUCCEEDED"],
        ),
        # trailing comma -- ignored
        ("FAILED,", ["FAILED"]),
    ),
)
def test_activity_notification_policy_parses_comma_delimited_opts(
    runner, input_str, parsed_as
):
    result = runner.invoke(simple_command, ["-o", input_str])
    expect_data = json.dumps({"status": parsed_as})
    assert result.output == f"filename: null\ndata: {expect_data}\n"


@pytest.mark.parametrize(
    "input_str, bad_values",
    (
        ("active", ["active"]),
        ("innactivve", ["innactivve"]),
        ("failure", ["failure"]),
        ("failure,success", ["failure", "success"]),
        ("failure,inactive,success", ["failure", "success"]),
    ),
)
def test_activity_notification_policy_rejects_unknown_comma_delimited_opts(
    runner, input_str, bad_values
):
    result = runner.invoke(simple_command, ["-o", input_str])
    assert result.exit_code == 2
    if len(bad_values) == 1:
        assert f"{bad_values[0]!r} was not a valid choice." in result.output
    else:
        assert f"{bad_values!r} were not valid choices." in result.output


def test_activity_notification_policy_can_parse_inline_json(runner):
    result = runner.invoke(simple_command, ["-o", '"baz"'])
    assert result.output == 'filename: null\ndata: "baz"\n'
    result = runner.invoke(simple_command, ["-o", '{"foo": 1}'])
    assert result.output == 'filename: null\ndata: {"foo": 1}\n'

    # notably, an inline 'null' will hit the parse-path for a comma-delimited list
    # and fail choice verification
    result = runner.invoke(simple_command, ["-o", "null"])
    assert result.exit_code == 2
    assert "'null' was not a valid choice." in result.output


def test_activity_notification_policy_rejects_invalid_inline_json(runner):
    # invalid JSON data causes errors
    result = runner.invoke(simple_command, ["-o", '{"foo": 1,}'])
    assert result.exit_code == 2
    assert "parameter value did not contain valid JSON" in result.output


def test_activity_notification_policy_can_parse_json_file(runner, tmpdir):
    # given the path to a file with valid JSON, it parses the result
    # functions with or without the `file:` prefix
    valid_file = tmpdir.mkdir("valid").join("file1.json")
    valid_file.write('{"foo": 1}\n')
    result = runner.invoke(simple_command, ["-o", "file:" + str(valid_file)])
    assert result.output == f'filename: {valid_file}\ndata: {{"foo": 1}}\n'
    result = runner.invoke(simple_command, ["-o", str(valid_file)])
    assert result.output == f'filename: {valid_file}\ndata: {{"foo": 1}}\n'


def test_activity_notification_policy_rejects_invalid_json_file(runner, tmpdir):
    # given the path to a file with invalid JSON, it raises an error
    invalid_file = tmpdir.mkdir("invalid").join("file1.json")
    invalid_file.write('{"foo": 1,}\n')
    result = runner.invoke(simple_command, ["-o", str(invalid_file)])
    assert result.exit_code == 2
    assert "did not contain valid JSON" in result.output


def test_activity_notification_policy_can_parse_json(runner, tmpdir):
    # given a path to a file which does not exist, it raises an appropriate error
    missing_file = tmpdir.join("missing.json")
    result = runner.invoke(simple_command, ["-o", "file:" + str(missing_file)])
    assert result.exit_code == 2
    assert "FileNotFound" in result.output
    assert "does not exist" in result.output

    # the same, but without the `file:` prefix
    result = runner.invoke(simple_command, ["-o", str(missing_file)])
    assert result.exit_code == 2
    assert "FileNotFound" in result.output
    assert "does not exist" in result.output


def test_activity_notification_policy_can_parse_json_from_stdin(runner, tmpdir):
    # can be given raw json objects on stdin and parses them faithfully
    result = runner.invoke(simple_command, ["-o", "-"], input="null\n")
    assert result.output == "filename: -\ndata: null\n"
    result = runner.invoke(simple_command, ["-o", "-"], input='"baz"\n')
    assert result.output == 'filename: -\ndata: "baz"\n'
    result = runner.invoke(simple_command, ["-o", "-"], input='{"foo": 1}\n')
    assert result.output == 'filename: -\ndata: {"foo": 1}\n'

    # and handles malformed inputs to stdin
    result = runner.invoke(simple_command, ["-o", "-"], input="[\n")
    assert result.exit_code == 2
    assert "stdin did not contain valid JSON" in result.output


@pytest.mark.skipif(sys.version_info < (3, 11), reason="contextlib.chdir added in 3.11")
def test_activity_notification_policy_completion_matches_files(
    get_completions, tmp_path
):
    file = tmp_path / "some_file.json"
    file.touch()
    with contextlib.chdir(tmp_path):
        completion_items = get_completions(
            simple_command, ["-o"], "some_", as_strings=False
        )
        assert len(completion_items) == 1
        result = completion_items[0]
        assert result.type == "file"
        assert result.value == "some_"


def test_activity_notification_policy_completion_expands_to_choices_with_no_input(
    get_completions,
):
    completion_items = get_completions(simple_command, ["-o"], "", as_strings=False)
    assert len(completion_items) == 3
    for result in completion_items:
        assert result.type == "plain"
    assert {result.value for result in completion_items} == {
        "INACTIVE",
        "SUCCEEDED",
        "FAILED",
    }


def test_activity_notification_policy_completion_expands_choice_list_one_result(
    get_completions,
):
    completion_items = get_completions(
        simple_command, ["-o"], "FAILED,I", as_strings=False
    )
    assert len(completion_items) == 1
    result = completion_items[0]
    assert result.type == "plain"
    assert result.value == "FAILED,INACTIVE"


def test_activity_notification_policy_completion_expands_choice_list_two_results(
    get_completions,
):
    completion_items = get_completions(
        simple_command, ["-o"], "FAILED,", as_strings=False
    )
    assert len(completion_items) == 2
    for result in completion_items:
        assert result.type == "plain"
    assert {result.value for result in completion_items} == {
        "FAILED,INACTIVE",
        "FAILED,SUCCEEDED",
    }
