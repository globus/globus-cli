"""
check annotations on click commands
requires python3.8+
"""

import datetime
import types
import typing as t
import uuid

import click

from globus_cli.constants import ExplicitNullType
from globus_cli.parsing.param_types import (
    CommaDelimitedList,
    EndpointPlusPath,
    IdentityType,
    JSONStringOrFile,
    LocationType,
    NotificationParamType,
    ParsedIdentity,
    StringOrNull,
    TaskPath,
    TimedeltaType,
    UrlOrNull,
)
from globus_cli.types import JsonValue


def _param2types(param_obj: click.Parameter) -> tuple[type, ...]:
    param_type = param_obj.type

    # click types
    if isinstance(param_type, click.types.StringParamType):
        return (str,)
    if isinstance(param_type, click.types.BoolParamType):
        return (bool,)
    elif isinstance(param_type, (click.types.IntParamType, click.IntRange)):
        return (int,)
    elif isinstance(param_type, (click.types.FloatParamType, click.FloatRange)):
        return (float,)
    elif isinstance(param_type, click.Choice):
        return (t.Literal[tuple(param_type.choices)],)
    elif isinstance(param_type, click.DateTime):
        return (datetime.datetime,)
    if isinstance(param_type, click.types.UUIDParameterType):
        return (uuid.UUID,)
    if isinstance(param_type, click.File):
        return (t.TextIO,)
    if isinstance(param_type, click.Path):
        if param_type.path_type is not None:
            if isinstance(param_obj.path_type, type):
                return (param_obj.path_type,)
            else:
                raise NotImplementedError(
                    "todo: support the return type of a converter func"
                )
        else:
            return (str,)

    # globus-cli types
    if isinstance(param_type, CommaDelimitedList):
        return (list[str],)
    elif isinstance(param_type, EndpointPlusPath):
        if param_type.path_required:
            return (tuple[uuid.UUID, str],)
        else:
            return (tuple[uuid.UUID, str | None],)
    elif isinstance(param_type, IdentityType):
        return (ParsedIdentity,)
    elif isinstance(param_type, JSONStringOrFile):
        return (JsonValue,)
    elif isinstance(param_type, LocationType):
        return (tuple[float, float],)
    elif isinstance(param_type, StringOrNull):
        return (str, ExplicitNullType)
    elif isinstance(param_type, UrlOrNull):
        return (str, ExplicitNullType)
    elif isinstance(param_type, TaskPath):
        return (TaskPath,)
    elif isinstance(param_type, NotificationParamType):
        return (dict[str, bool],)
    elif isinstance(param_type, TimedeltaType):
        if param_type._convert_to_seconds:
            return (int,)
        return (datetime.timedelta,)

    raise NotImplementedError(f"unsupported parameter type: {param_type}")


_NEVER_NULL_TYPES = (NotificationParamType,)


def check_has_correct_annotations_for_click_args(f):
    hints = t.get_type_hints(f.callback)
    param_map = {}
    for param in f.params:
        # skip params which do not get passed to the callback
        if param.expose_value is False:
            continue

        param_map[param.name] = param

    for name in param_map:
        if name not in hints:
            raise ValueError(f"expected parameter '{name}' was not in type hints")

    for name, param_obj in param_map.items():
        possible_types = set()
        # only implicitly add NoneType to the types if the default is None
        # some possible cases to consider:
        #   '--foo' is a string with an automatic default of None
        #   '--foo/--no-foo' is a bool flag with an automatic default of False
        #   '--foo/--no-foo' is a bool flag with an explicit default of None
        #   '--foo' is a count option with a default of 0
        #   '--foo' uses a param type which converts None to a default value
        if isinstance(param_obj, click.Option):
            if param_obj.default is None and not isinstance(
                param_obj.type, _NEVER_NULL_TYPES
            ):
                possible_types.add(None.__class__)

        for param_type in _param2types(param_obj):
            if param_obj.multiple:
                param_type = list[(param_type,)]
            possible_types.add(param_type)

        annotated_param_type = hints[name]
        annotation_base = t.get_origin(annotated_param_type)
        if (
            annotation_base is t.Union
            or annotation_base is types.UnionType  # noqa: E721
        ):
            annotated_types = t.get_args(annotated_param_type)
            if set(annotated_types) != possible_types:
                raise ValueError(
                    f"parameter '{name}' has unexpected parameter types "
                    f"'{annotated_types}' rather than '{possible_types}'"
                )
        else:
            if len(possible_types) != 1:
                raise ValueError(
                    f"parameter '{name}' has unexpected parameter types "
                    f"'{annotated_param_type}' rather than '{possible_types}'"
                )
            expected_type = possible_types.pop()
            if annotated_param_type != expected_type:
                raise ValueError(
                    f"parameter '{name}' has unexpected parameter types "
                    f"'{annotated_param_type}' rather than '{expected_type}'"
                )

    return True
