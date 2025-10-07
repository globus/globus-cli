from __future__ import annotations

import click
import pytest

from globus_cli.reflect import iter_all_commands
from globus_cli.types import JsonValue

click_type_test = pytest.importorskip(
    "click_type_test", reason="tests require 'click-type-test'"
)

_SKIP_MODULES = (
    "globus_cli.commands.timer.create.flow",
    "globus_cli.commands.timer.create.transfer",
    "globus_cli.commands.endpoint.permission.create",
    "globus_cli.commands.endpoint.role.create",
)

_ALL_NON_GROUP_COMMANDS: tuple[click.Command, ...] = (
    ctx.command
    for ctx in iter_all_commands(skip_hidden=False)
    if not isinstance(ctx.command, click.Group)
)
_ALL_COMMANDS_TO_TEST: tuple[tuple[str, str], ...] = (
    command
    for command in _ALL_NON_GROUP_COMMANDS
    if command.callback.__module__ not in _SKIP_MODULES
)


def _command_id_fn(val):
    assert isinstance(val, click.Command)
    return val.callback.__module__


@pytest.mark.parametrize("command", _ALL_COMMANDS_TO_TEST, ids=_command_id_fn)
def test_annotations_match_click_params(command):
    click_type_test.check_param_annotations(
        command, known_type_names={JsonValue: "globus_cli.types.JsonValue"}
    )
