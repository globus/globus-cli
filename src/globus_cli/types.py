"""
Internal types for type annotations
"""
from __future__ import annotations

import sys
import typing as t

import click

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

# runtime usable types (see AnnotatedOption for a use-case)
if sys.version_info >= (3, 9):
    DictType = dict
    ListType = list
    TupleType = tuple
else:
    DictType = t.Dict
    ListType = t.List
    TupleType = t.Tuple

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if t.TYPE_CHECKING:
    import globus_sdk

    from globus_cli.utils import CLIStubResponse


ClickContextTree: TypeAlias = t.Tuple[
    click.Context, t.List[click.Context], t.List["ClickContextTree"]
]


DATA_CONTAINER_T = t.Union[
    t.Mapping[str, t.Any],
    "globus_sdk.GlobusHTTPResponse",
    "CLIStubResponse",
]

JsonValue: TypeAlias = t.Union[
    int, float, str, bool, None, t.List["JsonValue"], t.Dict[str, "JsonValue"]
]


ServiceNameLiteral: TypeAlias = Literal[
    "auth", "transfer", "groups", "search", "timer", "flows"
]
