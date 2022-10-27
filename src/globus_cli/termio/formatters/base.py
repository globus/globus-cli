from __future__ import annotations

import abc
import typing as t
import warnings

T = t.TypeVar("T")


class FormattingFailedWarning(UserWarning):
    pass


class FieldFormatter(abc.ABC, t.Generic[T]):
    parse_null_values: bool = False

    def warn_formatting_failed(self, value: t.Any) -> None:
        warnings.warn(
            f"Formatting failed for '{value!r}' with formatter={self!r}",
            FormattingFailedWarning,
        )

    @abc.abstractmethod
    def parse(self, value: t.Any) -> T:
        """
        The `parse()` step is responsible for producing well-formed data for a field.
        For example, parsing may convert a dictionary or mapping to a tuple by pulling
        out the relevant fields and checking their types.

        If parsing fails for any reason, it should raise a ValueError.
        """

    @abc.abstractmethod
    def render(self, value: T) -> str:
        """
        The `render()` step is responsible taking data which has already been parsed
        and reshaped and converting it into a string.
        For example, rendering may comma-join an array of strings into a
        comma-delimited list.

        If rendering fails for any reason, it should raise a ValueError.
        """

    def format(self, value: t.Any) -> str:
        """
        Formatting data consists primarily of parsing and then rendering.
        If either step fails, the default behavior warns and falls back on str().
        """
        if value is None and self.parse_null_values is False:
            return "None"
        try:
            data = self.parse(value)
            return self.render(data)
        except ValueError:
            self.warn_formatting_failed(value)
            return str(value)
