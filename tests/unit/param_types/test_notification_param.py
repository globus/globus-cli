import click
import pytest

from globus_cli.parsing.param_types import NotificationParamType


@click.command()
@click.option(
    "--notify",
    type=NotificationParamType(),
    callback=NotificationParamType.STANDARD_CALLBACK,
)
def notify_cmd(notify):
    assert isinstance(notify, dict)
    click.echo(f"len(notify)={len(notify)}")
    for k in sorted(notify):
        click.echo(f"notify.{k}={notify[k]}")


def test_notify_no_opts(runner):
    # no arg becomes empty dict
    result = runner.invoke(notify_cmd, [])
    assert result.exit_code == 0
    assert result.output == "len(notify)=0\n"


@pytest.mark.parametrize("arg", ("", "off", "OFF", "Off"))
def test_notify_opt_off(runner, arg):
    result = runner.invoke(notify_cmd, ["--notify", arg])
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
    result = runner.invoke(notify_cmd, ["--notify", arg])
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
    result = runner.invoke(notify_cmd, ["--notify", arg])
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
    result = runner.invoke(notify_cmd, ["--notify", "whenever"])
    assert result.exit_code == 2
    assert "--notify received these invalid values: ['whenever']" in result.output


def test_notify_cannot_mix_opt_with_off(runner):
    # mixing off with other opts is rejected
    result = runner.invoke(notify_cmd, ["--notify", "off,inactive"])
    assert result.exit_code == 2
    assert '--notify cannot accept "off" and another value' in result.output


@pytest.mark.parametrize(
    "incomplete_value, expected_completions",
    (
        ("", {"on", "off", "succeeded", "failed", "inactive"}),
        ("o", {"on", "off"}),
        ("fail", {"failed"}),
        ("failed", {"failed"}),
        ("failed,inactive", {"failed,inactive"}),
        ("failed,inacti", {"failed,inactive"}),
        ("succeeded,", {"succeeded,failed", "succeeded,inactive"}),
        (",,succeeded,", {"succeeded,failed", "succeeded,inactive"}),
        (",,succeeded,,f", {"succeeded,failed"}),
        (",", {"succeeded", "failed", "inactive"}),
        ("succeeded,failed,inactive,", {"succeeded,failed,inactive"}),
        (",,,succeeded,,,,failed,inactive,", {"succeeded,failed,inactive"}),
        ("succeeded,UNKNOWN", {"succeeded,UNKNOWN"}),
        (",,succeeded,UNKNOWN", {"succeeded,UNKNOWN"}),
    ),
)
def test_notify_shell_complete(runner, incomplete_value, expected_completions):
    param_type = NotificationParamType()
    param = click.Option(["--notify"], type=param_type)
    completions = param_type.shell_complete(
        click.Context(notify_cmd), param, incomplete_value
    )
    got_values = {c.value for c in completions}
    assert got_values == expected_completions


def test_notify_metavar_in_help(runner):
    # running `--help` should show the custom metavar for `--notify`
    result = runner.invoke(notify_cmd, ["--help"])
    assert result.exit_code == 0
    assert "{on,off,succeeded,failed,inactive}" in result.output
