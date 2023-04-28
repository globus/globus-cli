import json

import click

from globus_cli.parsing import JSONStringOrFile, JSONStringOrFileV2, ParsedJSONData


def test_v1_json_string_or_file(runner, tmpdir):
    @click.command()
    @click.option("--bar", type=JSONStringOrFile(), default=None, help="a JSON blob")
    def foo(bar):
        click.echo(json.dumps(bar, sort_keys=True))

    # in helptext, it shows up with the correct metavar
    result = runner.invoke(foo, ["--help"])
    assert "--bar [JSON|file:JSON_FILE]" in result.output

    # absent, it leaves the default
    result = runner.invoke(foo, [])
    assert result.output == "null\n"

    # can be given raw json objects and parses them faithfully
    result = runner.invoke(foo, ["--bar", "null"])
    assert result.output == "null\n"
    result = runner.invoke(foo, ["--bar", '"baz"'])
    assert result.output == '"baz"\n'
    result = runner.invoke(foo, ["--bar", '{"foo": 1}'])
    assert result.output == '{"foo": 1}\n'

    # invalid JSON data causes errors
    result = runner.invoke(foo, ["--bar", '{"foo": 1,}'])
    assert result.exit_code == 2
    assert "the string '{\"foo\": 1,}' is not valid JSON" in result.output

    # something which looks like a file path but is malformed gives a specific error
    result = runner.invoke(foo, ["--bar", "file//1"])
    assert result.exit_code == 2
    assert (
        "the string 'file//1' is not valid JSON. Did you mean to use 'file:'?"
        in result.output
    )

    # given the path to a file with valid JSON, it parses the result
    valid_file = tmpdir.mkdir("valid").join("file1.json")
    valid_file.write('{"foo": 1}\n')
    result = runner.invoke(foo, ["--bar", "file:" + str(valid_file)])
    assert result.output == '{"foo": 1}\n'

    # given the path to a file with invalid JSON, it raises an error
    invalid_file = tmpdir.mkdir("invalid").join("file1.json")
    invalid_file.write('{"foo": 1,}\n')
    result = runner.invoke(foo, ["--bar", "file:" + str(invalid_file)])
    assert "did not contain valid JSON" in result.output

    # given a path to a file which does not exist, it raises an error
    missing_file = tmpdir.join("missing.json")
    result = runner.invoke(foo, ["--bar", "file:" + str(missing_file)])
    assert "FileNotFound" in result.output
    assert "does not exist" in result.output


def test_v2_json_string_or_file(runner, tmpdir):
    @click.command()
    @click.option("--bar", type=JSONStringOrFileV2(), default=None, help="a JSON blob")
    def foo(bar):
        if bar is None:
            click.echo("nil")
        else:
            assert isinstance(bar, ParsedJSONData)
            click.echo(f"filename: {bar.filename or 'null'}")
            click.echo(f"data: {json.dumps(bar.data, sort_keys=True)}")

    # in helptext, it shows up with the correct metavar
    result = runner.invoke(foo, ["--help"])
    assert "--bar [JSON_FILE|JSON|file:JSON_FILE]" in result.output

    # absent, it leaves the default
    result = runner.invoke(foo, [])
    assert result.output == "nil\n"

    # can be given raw json objects and parses them faithfully
    result = runner.invoke(foo, ["--bar", "null"])
    assert result.output == "filename: null\ndata: null\n"
    result = runner.invoke(foo, ["--bar", '"baz"'])
    assert result.output == 'filename: null\ndata: "baz"\n'
    result = runner.invoke(foo, ["--bar", '{"foo": 1}'])
    assert result.output == 'filename: null\ndata: {"foo": 1}\n'

    # invalid JSON data causes errors
    result = runner.invoke(foo, ["--bar", '{"foo": 1,}'])
    assert result.exit_code == 2
    assert "parameter value did not contain valid JSON" in result.output

    # given the path to a file with valid JSON, it parses the result
    # functions with or without the `file:` prefix
    valid_file = tmpdir.mkdir("valid").join("file1.json")
    valid_file.write('{"foo": 1}\n')
    result = runner.invoke(foo, ["--bar", "file:" + str(valid_file)])
    assert result.output == (f'filename: {valid_file}\ndata: {{"foo": 1}}\n')
    result = runner.invoke(foo, ["--bar", str(valid_file)])
    assert result.output == (f'filename: {valid_file}\ndata: {{"foo": 1}}\n')

    # given the path to a file with invalid JSON, it raises an error
    invalid_file = tmpdir.mkdir("invalid").join("file1.json")
    invalid_file.write('{"foo": 1,}\n')
    result = runner.invoke(foo, ["--bar", str(invalid_file)])
    assert "did not contain valid JSON" in result.output

    # given a path to a file which does not exist, it raises an appropriate error
    missing_file = tmpdir.join("missing.json")
    result = runner.invoke(foo, ["--bar", "file:" + str(missing_file)])
    assert "FileNotFound" in result.output
    assert "does not exist" in result.output
    # note that in this case, without the 'file:' prefix, this will actually start
    # out as a failed parse of JSON data as an argument, which then needs to be detected
    # as probably not JSON data, andemit the "right" error
    result = runner.invoke(foo, ["--bar", str(missing_file)])
    assert "FileNotFound" in result.output
    assert "does not exist" in result.output


def test_v2_json_string_or_file_handles_stdin(runner, tmpdir):
    @click.command()
    @click.option("--bar", type=JSONStringOrFileV2(), default=None, help="a JSON blob")
    def foo(bar):
        if bar is None:
            click.echo("nil")
        else:
            assert isinstance(bar, ParsedJSONData)
            click.echo(f"filename: {bar.filename or 'null'}")
            click.echo(f"data: {json.dumps(bar.data, sort_keys=True)}")

    # can be given raw json objects on stdin and parses them faithfully
    result = runner.invoke(foo, ["--bar", "-"], input="null\n")
    assert result.output == "filename: -\ndata: null\n"
    result = runner.invoke(foo, ["--bar", "-"], input='"baz"\n')
    assert result.output == 'filename: -\ndata: "baz"\n'
    result = runner.invoke(foo, ["--bar", "-"], input='{"foo": 1}\n')
    assert result.output == 'filename: -\ndata: {"foo": 1}\n'
