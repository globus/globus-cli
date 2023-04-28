import datetime

import click

from globus_cli.constants import EXPLICIT_NULL
from globus_cli.parsing import StringOrNull, TimedeltaType


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
