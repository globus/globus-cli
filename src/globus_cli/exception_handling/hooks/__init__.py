from __future__ import annotations

import typing as t

from ..registry import DeclaredHook, register_hook
from .auth_requirements import (
    consent_required_hook,
    handle_internal_auth_requirements,
    missing_login_error_hook,
    session_hook,
)
from .authapi_hooks import (
    authapi_hook,
    authapi_unauthenticated_hook,
    invalidrefresh_hook,
)
from .endpoint_types import wrong_endpoint_type_error_hook
from .flows_hooks import (
    flows_error_hook,
    flows_validation_error_hook,
    handle_flows_gare,
)
from .generic_hooks import (
    globus_error_hook,
    globusapi_hook,
    json_error_handler,
    null_data_error_handler,
)
from .search_hooks import searchapi_hook, searchapi_validationerror_hook
from .transfer_hooks import transfer_unauthenticated_hook, transferapi_hook


def register_all_hooks() -> None:
    """
    Load and register all hook functions.
    """
    for hook in _sort_all_hooks():
        register_hook(hook)


def _sort_all_hooks() -> t.Iterable[DeclaredHook[t.Any]]:
    """
    Iterate over all hooks in priority order.
    """
    # format as a list of lists for readability
    sorted_hook_collections: list[list[DeclaredHook[t.Any]]] = [
        # first, the generic hooks which filter out conditions
        # running 'null data' first ensures that every other
        # hook can assume that there is a JSON body
        # and running json_error_handler at the start means we know (in the
        # following hooks) that the output format is not JSON
        [null_data_error_handler, json_error_handler],
        # next, authn and session requirements, from most specific to most general
        [handle_internal_auth_requirements, handle_flows_gare],
        [session_hook, consent_required_hook],
        # CLI internal error types, which cannot be confused with external causes
        [missing_login_error_hook, wrong_endpoint_type_error_hook],
        # service-specific hooks uncaptured by earlier checks
        # each service has internal precedence ordering, but the collections could
        # probably be put in any order
        [authapi_unauthenticated_hook, invalidrefresh_hook, authapi_hook],
        [transfer_unauthenticated_hook, transferapi_hook],
        [flows_validation_error_hook, flows_error_hook],
        [searchapi_validationerror_hook, searchapi_hook],
        # finally, the catch-all hooks
        [globusapi_hook, globus_error_hook],
    ]

    for hook_collection in sorted_hook_collections:
        yield from hook_collection
