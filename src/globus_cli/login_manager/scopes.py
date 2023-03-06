from __future__ import annotations

import sys
import typing as t

from globus_sdk.scopes import (
    AuthScopes,
    FlowsScopes,
    GCSCollectionScopeBuilder,
    GroupsScopes,
    MutableScope,
    SearchScopes,
    TimerScopes,
    TransferScopes,
)

from globus_cli.types import ServiceNameLiteral

if sys.version_info < (3, 8):
    from typing_extensions import Final, TypedDict
else:
    from typing import Final, TypedDict

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


class _ServiceRequirement(TypedDict):
    min_contract_version: int
    resource_server: str
    scopes: list[str | MutableScope]


class _CLIScopeRequirements(t.Dict[ServiceNameLiteral, _ServiceRequirement]):
    def __init__(self) -> None:
        self["auth"] = {
            "min_contract_version": 0,
            "resource_server": AuthScopes.resource_server,
            "scopes": [
                AuthScopes.openid,
                AuthScopes.profile,
                AuthScopes.email,
                AuthScopes.view_identity_set,
            ],
        }
        self["transfer"] = {
            "min_contract_version": 0,
            "resource_server": TransferScopes.resource_server,
            "scopes": [
                TransferScopes.all,
            ],
        }
        self["groups"] = {
            "min_contract_version": 0,
            "resource_server": GroupsScopes.resource_server,
            "scopes": [
                GroupsScopes.all,
            ],
        }
        self["search"] = {
            "min_contract_version": 0,
            "resource_server": SearchScopes.resource_server,
            "scopes": [
                SearchScopes.all,
            ],
        }
        self["timer"] = {
            "min_contract_version": 1,
            "resource_server": TimerScopes.resource_server,
            "scopes": [
                TIMER_SCOPE_WITH_DEPENDENCIES,
            ],
        }
        self["flows"] = {
            "min_contract_version": 0,
            "resource_server": FlowsScopes.resource_server,
            "scopes": [
                FlowsScopes.manage_flows,
                FlowsScopes.view_flows,
                FlowsScopes.run,
                FlowsScopes.run_status,
                FlowsScopes.run_manage,
            ],
        }

    def resource_servers(self) -> frozenset[str]:
        return frozenset(req["resource_server"] for req in self.values())

    def get_by_resource_server(self, rs_name: str) -> _ServiceRequirement:
        for req in self.values():
            if req["resource_server"] == rs_name:
                return req

        raise LookupError(f"{rs_name} was not a listed service requirement for the CLI")


CLI_SCOPE_REQUIREMENTS = _CLIScopeRequirements()

# the contract version number for the LoginManager's scope behavior
# this will be annotated on every token acquired and stored, in order to see what
# version we were at when we got a token
# it should be the max of the version numbers required by the various different
# services
CURRENT_SCOPE_CONTRACT_VERSION: Final[int] = 1
