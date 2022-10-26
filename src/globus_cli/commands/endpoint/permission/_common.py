from __future__ import annotations

import typing as t

from globus_cli.termio import formatters


class AclPrincipalFormatter(formatters.PrincipalWithTypeKeyFormatter):
    # customize the formatter to provide the `principal_type` as the fallback value for
    # unrecognized types. This handles various cases in which
    # `principal_type=all_authenticated_users` or similar
    def parse(self, value: t.Any) -> tuple[str, str, str]:
        parsed_type, parsed_value, fallback = super().parse(value)
        return (parsed_type, parsed_value, parsed_type)
