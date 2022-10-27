from __future__ import annotations

from globus_cli.termio import formatters


class AclPrincipalFormatter(formatters.auth.PrincipalDictFormatter):
    # customize the formatter to provide the `principal_type` as the fallback value for
    # unrecognized types. This handles various cases in which
    # `principal_type=all_authenticated_users` or similar, which is the shape of the
    # data from Globus Transfer
    def fallback_rendering(self, principal: str, principal_type: str):
        return principal_type

    def render_group_id(self, group_id: str) -> str:
        return f"https://app.globus.org/groups/{group_id}"
