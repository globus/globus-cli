import click
import pytest

from globus_cli.parsing.known_callbacks import none_to_empty_dict
from globus_cli.parsing.param_types import NotificationParamType


@click.command()
@click.option("--notify", type=NotificationParamType(), callback=none_to_empty_dict)
def foo(notify):
    assert isinstance(notify, dict)
    click.echo(f"len(notify)={len(notify)}")
    for k in sorted(notify):
        click.echo(f"notify.{k}={notify[k]}")


def test_notify_no_opts(runner):
    # no arg becomes empty dict
    result = runner.invoke(foo, [])
    assert result.exit_code == 0
    assert result.output == "len(notify)=0\n"


@pytest.mark.parametrize("arg", ("", "off", "OFF", "Off"))
def test_notify_opt_off(runner, arg):
    result = runner.invoke(foo, ["--notify", arg])
    assert result.exit_code == 0
    assert (
        result.output
        == """\
len(notify)=3
notify.notify_on_failed=False
notify.notify_on_inactive=False
notify.notify_on_succeeded=False
"""
    )


@pytest.mark.parametrize("arg", ("on", "ON", "On", "on,failed", "succeeded , on"))
def test_notify_opt_on(runner, arg):
    result = runner.invoke(foo, ["--notify", arg])
    assert result.exit_code == 0
    assert result.output == "len(notify)=0\n"


@pytest.mark.parametrize(
    "arg, failed_val, inactive_val, succeeded_val",
    (
        ("failed", True, False, False),
        ("FAILED", True, False, False),
        ("Failed", True, False, False),
        ("inactive", False, True, False),
        ("INACTIVE", False, True, False),
        ("Inactive", False, True, False),
        ("succeeded", False, False, True),
        ("SUCCEEDED", False, False, True),
        ("Succeeded", False, False, True),
        ("failed,inactive", True, True, False),
        ("inactive,failed", True, True, False),
        ("failed,SUCCEEDED", True, False, True),
        ("succeeded,failed", True, False, True),
    ),
)
def test_notify_single_opt(runner, arg, failed_val, inactive_val, succeeded_val):
    result = runner.invoke(foo, ["--notify", arg])
    assert result.exit_code == 0
    assert (
        result.output
        == f"""\
len(notify)=3
notify.notify_on_failed={failed_val}
notify.notify_on_inactive={inactive_val}
notify.notify_on_succeeded={succeeded_val}
"""
    )


def test_notify_unrecognized_opt(runner):
    # invalid opts get rejected
    result = runner.invoke(foo, ["--notify", "whenever"])
    assert result.exit_code == 2
    assert "--notify received at least one invalid value" in result.output


def test_notify_cannot_mix_opt_with_off(runner):
    # mixing off with other opts is rejected
    result = runner.invoke(foo, ["--notify", "off,inactive"])
    assert result.exit_code == 2
    assert '--notify cannot accept "off" and another value' in result.output
