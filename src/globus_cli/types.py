"""
Internal types for type annotations
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Mapping, Tuple, Union

from globus_sdk import GlobusHTTPResponse

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if TYPE_CHECKING:
    from globus_cli.termio import FormatField
    from globus_cli.utils import CLIStubResponse


FIELD_T = Union[
    "FormatField",
    Tuple[str, str],
    Tuple[str, Callable[..., str]],
    # NOTE: this type is redundant with the previous two, but is needed to ensure
    # type agreement (mypy may flag it as a false negative otherwise)
    Tuple[str, Union[str, Callable[..., str]]],
]

FIELD_LIST_T = List[FIELD_T]

DATA_CONTAINER_T = Union[Mapping[str, Any], GlobusHTTPResponse, "CLIStubResponse"]
