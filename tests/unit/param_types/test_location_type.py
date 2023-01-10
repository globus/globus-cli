import click
import pytest

from globus_cli.parsing.param_types import LocationType


@click.command()
@click.argument(
    "LOCATION",
    type=LocationType(),
)
def loc_cmd(location):
    assert isinstance(location, str)
    click.echo(location)


@pytest.mark.parametrize(
    "loc_value",
    (
        ",1,1",
        "1,1,",
        ",1,1,",
        ",",
        "1,",
        ",1",
    ),
)
def test_location_cannot_parse_under_regex(runner, loc_value):
    # no arg becomes empty dict
    result = runner.invoke(loc_cmd, [loc_value])
    assert result.exit_code == 2
    assert "does not match the expected 'latitude,longitude' format" in result.output


@pytest.mark.parametrize(
    "loc_value",
    (
        "foo,bar",
        "10.0a,40.0",
        "10.0,40.0a",
    ),
)
def test_location_cannot_parse_as_float(runner, loc_value):
    # no arg becomes empty dict
    result = runner.invoke(loc_cmd, [loc_value])
    assert result.exit_code == 2
    assert "is not a well-formed 'latitude,longitude' pair" in result.output


@pytest.mark.parametrize(
    "loc_value",
    (
        "40,40.0",
        "10,-40.0",
        "-0.0,180.0",
        "190,255",  # not valid coordinates, but should parse okay
        "100 ,  20.0",
        "  100 ,  20.0  ",
        "  100.0,20.0  ",
    ),
)
def test_location_parses_okay(runner, loc_value):
    # no arg becomes empty dict
    result = runner.invoke(loc_cmd, ["--", loc_value])
    assert result.exit_code == 0, result.output
    assert result.output == f"{loc_value}\n"
