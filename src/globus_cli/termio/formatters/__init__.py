from . import auth
from .base import FieldFormatter, FormattingFailedWarning
from .compound import (
    ArrayFormatter,
    ParentheticalDescriptionFormatter,
    SortedJsonFormatter,
)
from .primitive import (
    BoolFormatter,
    DateFormatter,
    FuzzyBoolFormatter,
    StaticStringFormatter,
    StrFormatter,
)

Str = StrFormatter()
Date = DateFormatter()
Bool = BoolFormatter()
FuzzyBool = FuzzyBoolFormatter()
SortedJson = SortedJsonFormatter()
Array = ArrayFormatter()
SortedArray = ArrayFormatter(sort=True)

__all__ = (
    "FormattingFailedWarning",
    "FieldFormatter",
    "StrFormatter",
    "DateFormatter",
    "BoolFormatter",
    "FuzzyBoolFormatter",
    "StaticStringFormatter",
    "ArrayFormatter",
    "SortedJsonFormatter",
    "ParentheticalDescriptionFormatter",
    "Str",
    "Date",
    "Bool",
    "FuzzyBool",
    "SortedJson",
    "Array",
    "SortedArray",
    # directly re-expose this submodule as an attribute, allowing
    #   from globus_cli.termio import formatters
    #   ...
    #   x = formatters.auth.Foo()
    "auth",
)
