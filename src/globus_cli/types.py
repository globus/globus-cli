"""
Internal types for type annotations
"""
from __future__ import annotations

import typing as t

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if t.TYPE_CHECKING:
    import globus_sdk

    from globus_cli.termio import Field
    from globus_cli.utils import CLIStubResponse


FIELD_T = t.Union[
    "Field",
    t.Tuple[str, str],
    t.Tuple[str, t.Callable[..., str]],
    # NOTE: this type is redundant with the previous two, but is needed to ensure
    # type agreement (mypy may flag it as a false negative otherwise)
    t.Tuple[str, t.Union[str, t.Callable[..., str]]],
]

FIELD_LIST_T = t.Union[t.List[FIELD_T], t.List["Field"], t.List[t.Tuple[str, t.Any]]]

DATA_CONTAINER_T = t.Union[
    t.Mapping[str, t.Any],
    "globus_sdk.GlobusHTTPResponse",
    "CLIStubResponse",
]
