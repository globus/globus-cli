import click
import pytest

from globus_cli.parsing import CommaDelimitedList


def test_comma_delimited_list_help(runner):
    @click.command()
    @click.option("--foo", type=CommaDelimitedList(), help="a comma delimited list")
    def mycmd(foo):
        click.echo(foo)

    # in helptext, it shows up with "string,string,..." as the metavar
    result = runner.invoke(mycmd, ["--help"])
    assert "--foo TEXT,TEXT,...  a comma delimited list" in result.output


def test_comma_delimited_list_help_with_choices(runner):
    @click.command()
    @click.option("--foo", type=CommaDelimitedList(choices=("alpha", "beta")))
    def mycmd(foo):
        click.echo(foo)

    # in helptext, it shows up with "string,string,..." as the metavar
    result = runner.invoke(mycmd, ["--help"])
    assert "--foo {alpha,beta}" in result.output


@pytest.mark.parametrize(
    "add_args, expect_output",
    (
        # absent, it returns None
        ([], ("nil\n")),
        # given empty string (this is ambiguous!) returns empty array
        (["--foo", ""], "0\n"),
        # given one or more values, it listifies them
        (["--foo", "alpha"], "1\nalpha\n"),
        (["--foo", "alpha,beta"], "2\nalpha\nbeta\n"),
    ),
)
def test_comma_delimited_list_outputs(runner, add_args, expect_output):
    @click.command()
    @click.option("--foo", type=CommaDelimitedList(), default=None)
    def mycmd(foo):
        if foo is None:
            click.echo("nil")
        else:
            click.echo(len(foo))
            for x in foo:
                click.echo(x)

    result = runner.invoke(mycmd, add_args)
    assert result.output == expect_output
