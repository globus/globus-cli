"""
check annotations on click commands
requires python3.8+
"""
from __future__ import annotations

import datetime
import typing as t
import uuid

import click

from globus_cli.constants import ExplicitNullType
from globus_cli.parsing.known_callbacks import none_to_empty_dict
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


class BadAnnotationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        if len(errors) == 1:
            super().__init__(errors[0])
        else:
            super().__init__("\n  " + "\n  ".join(errors))


def _paramtypes_from_param_type(param_obj: click.Parameter) -> tuple[type, ...]:
    """
    Given a Parameter instance, read the 'type' attribute and deduce the tuple of
    possible types which it describes

    Supports both `click` native types and `globus_cli` custom types

    For example:
        IntParamType -> (int,)
        IntRange -> (int,)
        StringOrNull -> (str, None)

    Returning types as a tuple rather than building a union when there is more than one
    ensures that we build "flat" unions of the form `Union[x, y, z]` and avoid nested
    unions like `Union[x, Union[y, z]]`.
    """
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


_NEVER_NULL_CALLBACKS = (none_to_empty_dict,)


def _is_multi_param(p: click.Parameter) -> bool:
    if isinstance(p, click.Option) and p.multiple:
        return True

    if isinstance(p, click.Argument) and p.nargs == -1:
        return True

    return False


def _option_defaults_to_none(o: click.Option) -> bool:
    # if `default=1`, then the default can't be `None`
    if o.default is not None:
        return False

    # a multiple option defaults to () if default is unset or None
    if o.multiple:
        return False

    # got a known non-nullable callback? then it's not None
    if o.callback is not None and o.callback in _NEVER_NULL_CALLBACKS:
        return False

    # fallthrough case: True
    return True


def deduce_type_from_parameter(param: click.Paramter) -> type:
    """
    Convert a click.Paramter object to a type or union of types
    """
    possible_types = set()

    # only implicitly add NoneType to the types if the default is None
    # some possible cases to consider:
    #   '--foo' is a string with an automatic default of None
    #   '--foo/--no-foo' is a bool flag with an automatic default of False
    #   '--foo/--no-foo' is a bool flag with an explicit default of None
    #   '--foo' is a count option with a default of 0
    #   '--foo' uses a param type which converts None to a default value
    if isinstance(param, click.Option):
        if _option_defaults_to_none(param):
            possible_types.add(None.__class__)

    # if a parameter has `multiple=True` or `nargs=-1`, then the types which can be
    # deduced from the parameter should be exposed as an any-length tuple of unions
    if _is_multi_param(param):
        param_types_tuple = _paramtypes_from_param_type(param)
        if len(param_types_tuple) == 1:
            param_type = tuple[param_types_tuple[0], ...]
        else:
            param_type = tuple[t.Union[param_types_tuple], ...]
        possible_types.add(param_type)
    # if not multiple, then each of the possible types should be added to the
    # collection for a *potential* top-level union
    else:
        for param_type in _paramtypes_from_param_type(param):
            possible_types.add(param_type)

    # should be unreachable
    if len(possible_types) == 0:
        raise ValueError(f"parameter '{param.name}' had no deduced parameter types")

    # exactly one type: not a union, so unpack the only element
    if len(possible_types) == 1:
        return possible_types.pop()

    # more than one type: a union of the elements
    return t.Union[tuple(possible_types)]


def check_has_correct_annotations_for_click_args(f):
    hints = t.get_type_hints(f.callback)
    errors = []
    for param in f.params:
        # skip params which do not get passed to the callback
        if param.expose_value is False:
            continue
        if param.name not in hints:
            errors.append(f"expected parameter '{param.name}' was not in type hints")
            continue

        expected_type = deduce_type_from_parameter(param)
        annotated_param_type = hints[param.name]

        if annotated_param_type != expected_type:
            if expected_type == JsonValue:
                expected_type = "globus_cli.types.JsonValue"
            errors.append(
                f"parameter '{param.name}' has unexpected parameter type "
                f"'{annotated_param_type}' rather than '{expected_type}'"
            )
            continue

    if errors:
        raise BadAnnotationError(errors)

    return True
