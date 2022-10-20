from __future__ import annotations

import abc
import datetime
import enum
import typing as t


class FieldFormatter(abc.ABC):
    @abc.abstractmethod
    def format(self, value: t.Any) -> str | None:
        ...


class _StrFieldFormatter(FieldFormatter):
    def format(self, value: t.Any) -> str | None:
        return str(value)


class _DateFieldFormatter(FieldFormatter):
    def format(self, value: t.Any) -> str | None:
        if not value:
            return None
        # let this raise ValueError
        date = datetime.datetime.fromisoformat(value)
        if date.tzinfo is None:
            return date.strftime("%Y-%m-%d %H:%M:%S")
        return date.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _key_to_keyfunc(k):
    """
    We allow for 'keys' which are functions that map columns onto value
    types -- they may do formatting or inspect multiple values on the
    object. In order to support this, wrap string keys in a simple function
    that does the natural lookup operation, but return any functions we
    receive as they are.
    """
    # if the key is a string, then the "keyfunc" is just a basic lookup
    # operation -- return that
    if isinstance(k, str):
        subkeys = k.split(".")

        def lookup(x):
            current = x
            for sub in subkeys:
                current = x.get(sub)
                if current is None:
                    return None
            return current

        return lookup
    # otherwise, the key must be a function which is executed on the item
    # to produce a value -- return it verbatim
    return k


class Field:
    """A field which will be shown in record or table output.
    When fields are provided as tuples, they are converted into this.

    :param name: the displayed name for the record field or the column
        name for table output
    :param key: a str for indexing into print data or a callable which
        produces a string given the print data
    :param wrap_enabled: in record output, is this field allowed to wrap
    """

    class FormatName(enum.Enum):
        Str = enum.auto()
        Date = enum.auto()

    _DEFAULT_FORMATTERS: dict[FormatName, FieldFormatter] = {
        FormatName.Str: _StrFieldFormatter(),
        FormatName.Date: _DateFieldFormatter(),
    }

    def __init__(
        self,
        name,
        key,
        wrap_enabled=False,
        formatter: FormatName | FieldFormatter = FormatName.Str,
    ):
        self.name = name
        self.keyfunc = _key_to_keyfunc(key)
        self.wrap_enabled = wrap_enabled

        if isinstance(formatter, FieldFormatter):
            self.formatter: FieldFormatter = formatter
        elif isinstance(formatter, self.FormatName):
            self.formatter = self._DEFAULT_FORMATTERS[formatter]
        else:
            raise ValueError(f"bad field formatter: {formatter}")

    @classmethod
    def coerce(cls, rawfield):
        """given a (Field|tuple), convert to a Field"""
        if isinstance(rawfield, cls):
            return rawfield
        elif isinstance(rawfield, tuple):
            if len(rawfield) == 2:
                return cls(rawfield[0], rawfield[1])
            raise ValueError("cannot coerce tuple of bad length")
        raise TypeError(
            "Field.coerce must be given a field or tuple, "
            "got {}".format(type(rawfield))
        )

    def __call__(self, data):
        """extract the field's value from the data and format it"""
        return self.formatter.format(self.keyfunc(data))
