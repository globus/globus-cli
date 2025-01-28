from __future__ import annotations

import abc
import typing as t

import globus_sdk

from globus_cli.types import JsonValue

from ..context import get_jmespath_expression

DataType = t.TypeVar("DataType")


class Printer(abc.ABC, t.Generic[DataType]):

    @abc.abstractmethod
    def echo(self, data: DataType, stream: t.IO[str] | None = None) -> None:
        raise NotImplementedError

    @classmethod
    def jmespath_preprocess(
        cls, res: JsonValue | globus_sdk.GlobusHTTPResponse
    ) -> t.Any:
        jmespath_expr = get_jmespath_expression()

        if isinstance(res, globus_sdk.GlobusHTTPResponse):
            res = res.data

        if not isinstance(res, str):
            if jmespath_expr is not None:
                res = jmespath_expr.search(res)

        return res
