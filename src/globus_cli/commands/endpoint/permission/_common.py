from __future__ import annotations

from globus_cli.termio import formatters


class AclPrincipalFormatter(formatters.auth.PrincipalDictFormatter):
    # customize the formatter to provide the `principal_type` as the fallback value for
    # unrecognized types. This handles various cases in which
    # `principal_type=all_authenticated_users` or similar, which is the shape of the
    # data from Globus Transfer
    def fallback_rendering(self, principal: str, principal_type: str):
        return principal_type

    # TODO: re-assess Group rendering in the CLI
    # see also the implementation in the base class
    #
    # this URL is a real part of the webapp which displays info on a given group
    # it could be made multi-environment using `globus_sdk.config.get_webapp_url()`
    def render_group_id(self, group_id: str) -> str:
        return f"https://app.globus.org/groups/{group_id}"
