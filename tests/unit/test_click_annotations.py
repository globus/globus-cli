from __future__ import annotations

import typing as t

import click
import globus_sdk
import pytest

from globus_cli.commands.flows._common import SubscriptionIdType
from globus_cli.commands.flows.list import (
    ORDER_BY_FIELDS,
)
from globus_cli.commands.flows.list import list_command as flow_list_command
from globus_cli.parsing import CommaDelimitedList, OmittableChoice
from globus_cli.parsing.param_types.omittable import (
    OmittableDateTime,
    OmittableInt,
    OmittableString,
    OmittableUUID,
)
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

_ALL_NON_GROUP_COMMANDS: tuple[click.Command, ...] = tuple(
    ctx.command
    for ctx in iter_all_commands(skip_hidden=False)
    if not isinstance(ctx.command, click.Group)
)
_ALL_COMMANDS_TO_TEST: tuple[click.Command, ...] = tuple(
    command
    for command in _ALL_NON_GROUP_COMMANDS
    if command.callback.__module__ not in _SKIP_MODULES
)


_OVERRIDES = {
    flow_list_command: {
        "orderby": tuple[
            tuple[
                t.Literal[ORDER_BY_FIELDS],
                t.Literal["ASC", "DESC"],
            ],
            ...,
        ]
    }
}


def _command_id_fn(val):
    assert isinstance(val, click.Command)
    return val.callback.__module__


@pytest.mark.parametrize("command", _ALL_COMMANDS_TO_TEST, ids=_command_id_fn)
def test_annotations_match_click_params(command):
    overrides = _OVERRIDES.get(command, {})
    click_type_test.check_param_annotations(
        command,
        known_type_names={JsonValue: "globus_cli.types.JsonValue"},
        overrides=overrides,
    )


@pytest.mark.parametrize("command", _ALL_COMMANDS_TO_TEST, ids=_command_id_fn)
def test_omittables_are_omittable(command):
    """
    Developer sanity check: ensure that every click option with a default of
    ``globus_sdk.MISSING`` is correctly typed as an "omittable" type, and vice versa.
    """

    for param in command.params:
        does_default_to_missing = param.default is globus_sdk.MISSING
        is_omittable = _is_omittable_param_type(param.type)

        if is_omittable and not does_default_to_missing:
            pytest.fail(
                f"Parameter '{param.name}' in command '{command.name}' is declared as"
                f"an omittable type ({param.type!r}) but does not default to "
                f"`globus_sdk.MISSING` (default: {param.default!r})."
            )
        elif not is_omittable and does_default_to_missing:
            pytest.fail(
                f"Parameter '{param.name}' in command '{command.name}' defaults to "
                f"`globus_sdk.MISSING` but is not declared as an omittable type "
                f"({param.type!r})."
            )


_OmittableTypes = (
    OmittableInt,
    OmittableString,
    OmittableUUID,
    OmittableChoice,
    OmittableDateTime,
)


def _is_omittable_param_type(param_type: click.ParamType) -> bool:
    """Determine if a click.ParamType is an "omittable" type."""

    for omittable_type in _OmittableTypes:
        if isinstance(param_type, omittable_type):
            return True

    if isinstance(param_type, CommaDelimitedList) and param_type._omittable:
        return True

    if isinstance(param_type, SubscriptionIdType) and param_type._omittable:
        return True

    return False
