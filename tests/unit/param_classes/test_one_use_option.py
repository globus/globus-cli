import click
import pytest

from globus_cli.parsing.param_classes import OneUseOption, one_use_option


def test_one_use_option_multiple_allows_unused(runner):
    @click.command()
    @click.option("--foo", multiple=True, cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    result = runner.invoke(testcmd, [])
    assert result.exit_code == 0
    assert result.output == "\n"


def test_one_use_option_multiple_allows_single_use(runner):
    @click.command()
    @click.option("--foo", multiple=True, cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    result = runner.invoke(testcmd, ["--foo", "a"])
    assert result.exit_code == 0
    assert result.output == "a\n"


def test_one_use_option_multiple_rejects_opt_used_twice(runner):
    @click.command()
    @click.option("--foo", multiple=True, cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    result = runner.invoke(testcmd, ["--foo", "a", "--foo", "b"])
    assert result.exit_code == 2
    assert "Option used multiple times" in result.output


def test_one_use_option_count_allows_unused(runner):
    @click.command()
    @click.option("--foo", count=True, cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    result = runner.invoke(testcmd, [])
    assert result.exit_code == 0
    assert result.output == "False\n"


def test_one_use_option_count_allows_used_once(runner):
    @click.command()
    @click.option("--foo", count=True, cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    result = runner.invoke(testcmd, ["--foo"])
    assert result.exit_code == 0
    assert result.output == "True\n"


def test_one_use_option_count_rejects_opt_used_twice(runner):
    @click.command()
    @click.option("--foo", count=True, cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    result = runner.invoke(testcmd, ["--foo", "--foo"])
    assert result.exit_code == 2
    assert "Option used multiple times" in result.output


def test_one_use_option_fails_if_neither_count_nor_multiple(runner):
    @click.command()
    @click.option("--foo", cls=OneUseOption)
    def testcmd(foo):
        click.echo(foo)

    with pytest.raises(
        ValueError,
        match="Internal error, OneUseOption expected either multiple or count",
    ):
        runner.invoke(testcmd, ["--foo", "bar"], catch_exceptions=False)


@pytest.mark.parametrize("kwargs", ({"multiple": True}, {"count": True}))
def test_one_use_option_decorator_rejects_params(kwargs):
    with pytest.raises(ValueError, match="cannot be used with multiple or count"):
        one_use_option("--foo", **kwargs)


def test_one_use_option_decorator_rejects_alternate_cls():
    with pytest.raises(ValueError, match="cannot overwrite cls"):
        one_use_option("--foo", cls=click.Option)
