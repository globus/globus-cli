from __future__ import annotations

import typing as t

from . import formatters


class Field:
    """A field which will be shown in record or table output.
    When fields are provided as tuples, they are converted into this.

    :param name: the displayed name for the record field or the column
        name for table output
    :param key: a jmespath expression for indexing into print data
    :param wrap_enabled: in record output, is this field allowed to wrap
    """

    def __init__(
        self,
        name: str,
        key: str,
        *,
        wrap_enabled: bool = False,
        formatter: formatters.FieldFormatter[t.Any] = formatters.Str,
    ) -> None:
        self.name = name
        self.key = key
        self.wrap_enabled = wrap_enabled
        self.formatter = formatter

    def get_value(self, data: t.Any) -> t.Any:
        import jmespath

        return jmespath.search(self.key, data)

    def format(self, value: t.Any) -> str:
        return self.formatter.format(value)

    def serialize(self, data: t.Any) -> str:
        return self.format(self.get_value(data))
