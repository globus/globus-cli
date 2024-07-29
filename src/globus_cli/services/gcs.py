from __future__ import annotations

import typing as t

import globus_sdk

from globus_cli.endpointish import Endpointish
from globus_cli.termio import formatters


class ConnectorIdFormatter(formatters.StrFormatter):
    def parse(self, value: t.Any) -> str:
        if not isinstance(value, str):
            raise ValueError("bad connector ID")
        connector = globus_sdk.ConnectorTable.lookup(value)
        if not connector:
            return f"UNKNOWN ({value})"
        return connector.name


class CustomGCSClient(globus_sdk.GCSClient):
    def __init__(
        self, *args: t.Any, source_epish: Endpointish, **kwargs: t.Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.source_epish = source_epish
