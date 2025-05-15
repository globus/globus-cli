"""
Global interface for managing accessing and modifying terminal info.

Some printers and formatters within this termio module are concerned with text wrapping.
To do this effectively, they need to know where exactly to start wrapping text.
"""

from __future__ import annotations

import contextlib
import shutil
import typing as t
from textwrap import TextWrapper

__all__ = ("TERM_INFO", "TerminalTextWrapper")


class VirtualTerminalInfo:
    MIN_COLUMNS = 6

    def __init__(self) -> None:
        self._column_delta = 0
        cols, rows = shutil.get_terminal_size(fallback=(80, 20))
        self._base_columns = cols if cols < 100 else int(0.8 * cols)
        self._base_rows = rows

    @contextlib.contextmanager
    def indented(self, size: int) -> t.Iterator[None]:
        """
        Context manager to temporarily decrease the available width for text wrapping.
        """
        self._column_delta -= size
        try:
            yield
        finally:
            self._column_delta += size

    @property
    def columns(self) -> int:
        computed_columns = self._base_columns + self._column_delta
        return max(self.MIN_COLUMNS, computed_columns)


class TerminalTextWrapper(TextWrapper):
    """
    A text wrapper customized for wrapping text to the terminal.

    If width is not supplied, it will be evaluated from ``TERM_INFO``.
    """

    def __init__(self, *args: t.Any, width: int | None = None, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._width = width

    @property
    def width(self) -> int:
        return self._width or TERM_INFO.columns

    @width.setter
    def width(self, value: int) -> None:
        self._width = value


TERM_INFO = VirtualTerminalInfo()
