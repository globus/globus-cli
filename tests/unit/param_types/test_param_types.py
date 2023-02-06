import datetime
import json

import click

from globus_cli.constants import EXPLICIT_NULL
from globus_cli.parsing import (
    CommaDelimitedList,
    JSONStringOrFile,
    StringOrNull,
    TimedeltaType,
)
from globus_cli.parsing.param_types.prefix_mapper import StringPrefixMapper


def test_string_or_null(runner):
    @click.command()
    @click.option(
        "--bar", type=StringOrNull(), default=None, help="a string or null value"
    )
    def foo(bar):
        if bar is None:
            click.echo("none")
        elif bar is EXPLICIT_NULL:
            click.echo("null")
        else:
            click.echo(bar)

    # in helptext, it shows up with "string" as the metavar
    result = runner.invoke(foo, ["--help"])
    assert "--bar TEXT  a string or null value" in result.output

    # absent, it returns None
    result = runner.invoke(foo, [])
    assert result.output == "none\n"

    # given empty string returns explicit null value
    result = runner.invoke(foo, ["--bar", ""])
    assert result.output == "null\n"

    # given a string, it returns that string
    result = runner.invoke(foo, ["--bar", "alpha"])
    assert result.output == "alpha\n"


def test_comma_delimited_list(runner):
    @click.command()
    @click.option(
        "--bar", type=CommaDelimitedList(), default=None, help="a comma delimited list"
    )
    def foo(bar):
        if bar is None:
            click.echo("nil")
        else:
            click.echo(len(bar))
            for x in bar:
                click.echo(x)

    # in helptext, it shows up with "string,string,..." as the metavar
    result = runner.invoke(foo, ["--help"])
    assert "--bar TEXT,TEXT,...  a comma delimited list" in result.output

    # absent, it returns None
    result = runner.invoke(foo, [])
    assert result.output == "nil\n"

    # given empty string (this is ambiguous!) returns empty array
    result = runner.invoke(foo, ["--bar", ""])
    assert result.output == "0\n"

    # given "alpha" it returns "['alpha']"
    result = runner.invoke(foo, ["--bar", "alpha"])
    assert result.output == "1\nalpha\n"

    # given a UUID it returns that UUID
    result = runner.invoke(foo, ["--bar", "alpha,beta"])
    assert result.output == "2\nalpha\nbeta\n"


def test_string_prefix_mapper(runner, tmpdir):
    class MyType(StringPrefixMapper):
        __prefix_mapping__ = {"bar:": "prefix_mapper_parse_bar"}
        __prefix_metavars__ = ["bar:BAR", "BAZ"]

        def prefix_mapper_parse_bar(self, value):
            if not value.startswith("BARBAR"):
                raise click.UsageError("malformed BarObject")
            return value[len("BARBAR") :]

    @click.command()
    @click.option("--bar", type=MyType(null="NIL"), default=None, help="a BarObject")
    def foo(bar):
        if bar is None:
            click.echo("nil")
        else:
            click.echo(bar)

    # in helptext, it shows up with the correct metavar
    result = runner.invoke(foo, ["--help"])
    assert "--bar [bar:BAR|BAZ]" in result.output

    # absent, it leaves the default
    result = runner.invoke(foo, [])
    assert result.output == "nil\n"

    # supports explicit null value as well
    result = runner.invoke(foo, ["--bar", "NIL"])
    assert result.output == "null\n"

    # does nothing when the value is neither the null value nor has the prefix
    result = runner.invoke(foo, ["--bar", "foo:bar"])
    assert result.output == "foo:bar\n"

    # but with the prefix, behaves as expected
    result = runner.invoke(foo, ["--bar", "bar:BARBARbaz"])
    assert result.output == "baz\n"


def test_json_string_or_file(runner, tmpdir):
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


def test_timedelta_type(runner):
    @click.command()
    @click.argument("t", type=TimedeltaType())
    def foo(t):
        click.echo(f"t={t}")

    # various individual time units in seconds
    for arg, val in (
        # 10 seconds is 10 seconds
        ("10s", 10),
        # 2 minutes is 2 * 60 = 120 seconds
        ("2m", 120),
        # 1 hour is 3600 seconds
        ("1h", 3600),
        # 3 days is 72 hours is 72 * 3600 seconds
        ("3d", 72 * 3600),
        # 5 weeks is 5 * 7 * 24 hours is 5 * 7 * 24 * 3600 seconds
        ("5w", 5 * 7 * 24 * 3600),
    ):
        result = runner.invoke(foo, [arg])
        assert result.output == f"t={val}\n"

    # combined values
    for arg, val in (
        # 1 minutes 10 seconds is 70 seconds
        ("1m10s", 70),
        # 2 weeks 3 days 4 hours 5 minutes 6 seconds
        # is
        #   2 * 7 * 24 * 60 * 60
        # + 3 * 24 * 60 * 60
        # + 4 * 60 * 60
        # + 5 * 60
        # + 6
        ("2w3d4h5m6s", (5 + (4 + (3 + 2 * 7) * 24) * 60) * 60 + 6),
    ):
        result = runner.invoke(foo, [arg])
        assert result.output == f"t={val}\n"

    # with surrounding and interspersed whitespace
    result = runner.invoke(foo, [" 2d  3m1s"])
    assert result.output == f"t={1 + 3 * 60 + 2 * 24 * 3600}\n"

    # a bare integer is rejected
    result = runner.invoke(foo, ["100"])
    assert result.exit_code == 2
    assert "couldn't parse timedelta: '100'" in result.output

    # out of order fails to parse
    result = runner.invoke(foo, ["1m2d"])
    assert result.exit_code == 2
    assert "couldn't parse timedelta: '1m2d'" in result.output

    # unrecognized duration chars fail to parse
    result = runner.invoke(foo, ["1y"])
    assert result.exit_code == 2
    assert "couldn't parse timedelta: '1y'" in result.output

    # not converted back to seconds, alternate command
    @click.command()
    @click.argument("t", type=TimedeltaType(convert_to_seconds=False))
    def bar(t):
        assert isinstance(t, datetime.timedelta)
        click.echo(f"delta={t}")

    result = runner.invoke(bar, ["2h1m"])
    assert result.output == "delta=2:01:00\n"
