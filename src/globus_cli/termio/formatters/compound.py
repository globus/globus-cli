from __future__ import annotations

import json
import typing as t

from .base import FieldFormatter
from .primitive import StrFormatter

JSON = t.Union[None, bool, dict, float, int, list, str]


class SortedJsonFormatter(FieldFormatter[JSON]):
    parse_null_values = True

    def parse(self, value: t.Any) -> JSON:
        if value is None or isinstance(value, (bool, dict, float, int, list, str)):
            return t.cast(JSON, value)
        raise ValueError("bad JSON value")

    def render(self, value: JSON) -> str:
        return json.dumps(value, sort_keys=True)


class ArrayFormatter(FieldFormatter[t.List[str]]):
    def __init__(
        self,
        *,
        delimiter: str = ",",
        sort: bool = False,
        element_formatter: FieldFormatter | None = None,
    ) -> None:
        self.delimiter = delimiter
        self.sort = sort
        self.element_formatter: FieldFormatter = (
            element_formatter if element_formatter is not None else StrFormatter()
        )

    def parse(self, value: t.Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("non list array value")
        data = [self.element_formatter.format(x) for x in value]
        if self.sort:
            return sorted(data)
        else:
            return data

    def render(self, value: list[str]) -> str:
        return self.delimiter.join(value)


class ParentheticalDescriptionFormatter(FieldFormatter[t.Tuple[str, str]]):
    def parse(self, value: t.Any) -> tuple[str, str]:
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(
                "cannot format parenthetical description from data of wrong shape"
            )
        main, description = value[0], value[1]
        if not isinstance(main, str) or not isinstance(description, str):
            raise ValueError("cannot format parenthetical description non-str data")
        return (main, description)

    def render(self, value: tuple[str, str]) -> str:
        return f"{value[0]} ({value[1]})"
