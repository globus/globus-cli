"""
Internal types for type annotations
"""

from __future__ import annotations

import sys
import typing as t

import click

if sys.version_info >= (3, 10):
    from typing import TypeAlias, TypeGuard
else:
    from typing_extensions import TypeAlias, TypeGuard

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if t.TYPE_CHECKING:
    import globus_sdk


AnyCallable: TypeAlias = t.Callable[..., t.Any]
AnyCommand: TypeAlias = t.Union[click.Command, AnyCallable]


ClickContextTree: TypeAlias = t.Tuple[
    click.Context, t.List[click.Context], t.List["ClickContextTree"]
]


DATA_CONTAINER_T: TypeAlias = t.Union[
    t.Mapping[str, t.Any],
    "globus_sdk.GlobusHTTPResponse",
]


JsonDict: TypeAlias = t.Dict[str, "JsonValue"]
JsonList: TypeAlias = t.List["JsonValue"]
JsonValue: TypeAlias = t.Union[int, float, str, bool, None, JsonList, JsonDict]


def is_json_value(value: t.Any) -> TypeGuard[JsonValue]:
    """
    A typeguard for JsonValue.
    If the JsonValue is > 100 levels nested deep, it will be considered a JsonValue.
    """
    return _is_json_value(value, max_depth=100)


def _is_json_value(value: t.Any, max_depth: int) -> TypeGuard[JsonValue]:
    if max_depth == 0:
        return True

    if isinstance(value, (int, float, str, bool, type(None))):
        return True
    depth = max_depth - 1
    return _is_json_list(value, max_depth=depth) or _is_json_dict(
        value, max_depth=depth
    )


def is_json_dict(value: t.Any) -> TypeGuard[JsonDict]:
    """
    A typeguard for JsonDict.
    If the JsonDict is > 100 levels nested deep, it will be considered a JsonDict.
    """
    return _is_json_dict(value, max_depth=100)


def _is_json_dict(value: t.Any, max_depth: int) -> TypeGuard[JsonDict]:
    if max_depth == 0:
        return True

    if not isinstance(value, dict):
        return False
    depth = max_depth - 1
    return all(
        isinstance(k, str) and _is_json_value(v, max_depth=depth)
        for k, v in value.items()
    )


def is_json_list(value: t.Any) -> TypeGuard[JsonList]:
    """
    A typeguard for JsonList.
    If the JsonList is > 100 levels nested deep, it will be considered a JsonList.
    """
    return _is_json_list(value, max_depth=100)


def _is_json_list(value: t.Any, max_depth: int) -> TypeGuard[JsonList]:
    if max_depth == 0:
        return True

    if not isinstance(value, list):
        return False
    return all(is_json_value(item) for item in value)


ServiceNameLiteral: TypeAlias = t.Literal[
    "auth", "transfer", "groups", "search", "timers", "flows"
]
