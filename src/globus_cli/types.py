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

    from globus_cli.utils import CLIStubResponse


DATA_CONTAINER_T = t.Union[
    t.Mapping[str, t.Any],
    "globus_sdk.GlobusHTTPResponse",
    "CLIStubResponse",
]
