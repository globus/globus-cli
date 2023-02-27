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
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

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


class _CLIScopeRequirements:
    def __init__(self) -> None:
        self.requirement_map: dict[ServiceNameLiteral, _ServiceRequirement] = {
            "auth": {
                "min_contract_version": 0,
                "resource_server": AuthScopes.resource_server,
                "scopes": [
                    AuthScopes.openid,
                    AuthScopes.profile,
                    AuthScopes.email,
                    AuthScopes.view_identity_set,
                ],
            },
            "transfer": {
                "min_contract_version": 0,
                "resource_server": TransferScopes.resource_server,
                "scopes": [
                    TransferScopes.all,
                ],
            },
            "groups": {
                "min_contract_version": 0,
                "resource_server": GroupsScopes.resource_server,
                "scopes": [
                    GroupsScopes.all,
                ],
            },
            "search": {
                "min_contract_version": 0,
                "resource_server": SearchScopes.resource_server,
                "scopes": [
                    SearchScopes.all,
                ],
            },
            "timer": {
                "min_contract_version": 1,
                "resource_server": TimerScopes.resource_server,
                "scopes": [
                    TIMER_SCOPE_WITH_DEPENDENCIES,
                ],
            },
            "flows": {
                "min_contract_version": 0,
                "resource_server": FlowsScopes.resource_server,
                "scopes": [
                    FlowsScopes.manage_flows,
                    FlowsScopes.view_flows,
                    FlowsScopes.run,
                    FlowsScopes.run_status,
                    FlowsScopes.run_manage,
                ],
            },
        }

    def __getitem__(self, key: ServiceNameLiteral) -> _ServiceRequirement:
        return self.requirement_map[key]

    def get_by_resource_server(self, rs_name: str) -> _ServiceRequirement:
        for req in self.requirement_map.values():
            if req["resource_server"] == rs_name:
                return req

        raise LookupError(f"{rs_name} was not a listed service requirement for the CLI")

    def __contains__(self, key: str) -> bool:
        return key in self.requirement_map

    def resource_servers(self) -> frozenset[str]:
        return frozenset(req["resource_server"] for req in self.values())

    def keys(self) -> t.Iterable[ServiceNameLiteral]:
        yield from self.requirement_map.keys()

    def values(self) -> t.Iterable[_ServiceRequirement]:
        yield from self.requirement_map.values()


CLI_SCOPE_REQUIREMENTS = _CLIScopeRequirements()

# the contract version number for the LoginManager's scope behavior
# this will be annotated on every token acquired and stored, in order to see what
# version we were at when we got a token
# it is defined as the max of the version numbers required by the various different
# services
CURRENT_SCOPE_CONTRACT_VERSION: int = max(
    req["min_contract_version"] for req in CLI_SCOPE_REQUIREMENTS.values()
)
