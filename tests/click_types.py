"""
check annotations on click commands
requires python3.8+
"""
from __future__ import annotations

import datetime
import types
import typing as t
import uuid

import click

from globus_cli.parsing.param_classes import AnnotatedOption
from globus_cli.parsing.param_types import AnnotatedParamType
from globus_cli.types import JsonValue


class BadAnnotationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        if len(errors) == 1:
            super().__init__(errors[0])
        else:
            super().__init__("\n  " + "\n  ".join(errors))


_CLICK_STATIC_TYPE_MAP: dict[type[click.ParamType], type] = {
    click.types.StringParamType: str,
    click.types.BoolParamType: bool,
    click.types.IntParamType: int,
    click.IntRange: int,
    click.types.FloatParamType: float,
    click.FloatRange: float,
    click.DateTime: datetime.datetime,
    click.types.UUIDParameterType: uuid.UUID,
    click.File: t.TextIO,
}


def _type_from_param_type(param_obj: click.Parameter) -> type:
    """
    Given a Parameter instance, read the 'type' attribute and deduce the type or union
    of possible types which it describes

    Supports both `click` native types and `globus_cli` custom types

    For example:
        IntParamType -> int
        IntRange -> int
        StringOrNull -> str | ExplicitNullType
    """
    param_type = param_obj.type

    # globus-cli types
    if isinstance(param_type, AnnotatedParamType):
        return param_type.get_type_annotation(param_obj)

    # click types
    if type(param_type) in _CLICK_STATIC_TYPE_MAP:
        return _CLICK_STATIC_TYPE_MAP[type(param_type)]
    if isinstance(param_type, click.Choice):
        return t.Literal[tuple(param_type.choices)]
    if isinstance(param_type, click.Path):
        if param_type.path_type is not None:
            if isinstance(param_obj.path_type, type):
                return param_obj.path_type
            else:
                raise NotImplementedError(
                    "todo: support the return type of a converter func"
                )
        else:
            return str

    raise NotImplementedError(f"unsupported parameter type: {param_type}")


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

    # fallthrough case: True
    return True


def deduce_type_from_parameter(param: click.Parameter) -> type:
    """
    Convert a click.Parameter object to a type or union of types
    """
    # if there is an explicit annotation, use that
    if isinstance(param, AnnotatedOption) and param.has_explicit_annotation():
        return param.type_annotation

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

    # if a parameter has `multiple=True` or `nargs=-1`, then the type which can be
    # deduced from the parameter should be exposed as an any-length tuple
    if _is_multi_param(param):
        param_type = tuple[_type_from_param_type(param), ...]
        possible_types.add(param_type)
    # if not multiple, then the type may need to be unioned with `None`
    # but if the type is, itself, a union, then it will need to be unpacked
    else:
        param_type = _type_from_param_type(param)
        if (  # detect Union[X, Y] and "union type expressions" (X | Y)
            isinstance(param_type, types.UnionType)
            or t.get_origin(param_type) == t.Union
        ):
            for member_type in t.get_args(param_type):
                possible_types.add(member_type)
        else:
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
