from __future__ import annotations

import typing as t

from globus_sdk.scopes import (
    GCSCollectionScopeBuilder,
    MutableScope,
    TimerScopes,
    TransferScopes,
)

TRANSFER_AP_SCOPE_STR: str = (
    "https://auth.globus.org/scopes/actions.globus.org/transfer/transfer"
)


def compute_timer_scope(
    *, data_access_collection_ids: t.Sequence[str] | None = None
) -> MutableScope:
    transfer_scope = TransferScopes.make_mutable("all")
    for cid in data_access_collection_ids or ():
        transfer_scope.add_dependency(
            GCSCollectionScopeBuilder(cid).make_mutable("data_access", optional=True)
        )

    transfer_ap_scope = MutableScope(TRANSFER_AP_SCOPE_STR)
    transfer_ap_scope.add_dependency(transfer_scope)

    timer_scope = TimerScopes.make_mutable("timer")
    timer_scope.add_dependency(transfer_ap_scope)
    return timer_scope


# with no args, this builds
#   timer[transferAP[transfer]]
TIMER_SCOPE_WITH_DEPENDENCIES = compute_timer_scope()
