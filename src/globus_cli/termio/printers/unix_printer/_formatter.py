from __future__ import annotations

import sys
import typing as t
from itertools import chain

import click

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


Scalar: TypeAlias = "str | int | float | bool | None"
NonScalar: TypeAlias = "list[Scalar | NonScalar] | dict[str, Scalar | NonScalar]"


class UnixFormattingError(ValueError):
    """Class of errors indicating that the data could not be formatted."""


def unix_display(data: Scalar | NonScalar, stream: t.IO[str] | None = None) -> None:
    """
    Format an object in 'UNIX' format, writing it to some stream output.
    """
    for line in emit_any_value(data):
        click.echo(line, file=stream)


def emit_any_value(item: Scalar | NonScalar) -> t.Iterator[str]:
    """
    Emission of values is defined as yielding back each line of output.

    Lists and dicts are handled specially. Any scalar value is just passed to Python
    ``str()``. Note that this means that null becomes "None" in our output.
    """
    if isinstance(item, list):
        yield from emit_list(item)
    elif isinstance(item, dict):
        yield from emit_dict(item)
    else:
        yield str(item)


def emit_list(
    elements: list[Scalar | NonScalar],
    identifier: str | None = None,
) -> t.Iterator[str]:
    """
    Given a list, and optionally some identifier used to tag the output, emit lines of
    output.

    Supports:
        list[dict] , list[scalar] , and list[list | scalar]

    If the input mixes dicts and non-dict values, this function will raise a ValueError.
    """
    # empty lists disappear in the output
    if not elements:
        return

    # across these branches, mypy does not correctly narrow the type of `elements`
    # so we need to type-ignore the argument type
    if all(isinstance(item, dict) for item in elements):
        yield from emit_list_of_dicts(
            elements,  # type: ignore[arg-type]
            identifier=identifier,
        )
    elif any(isinstance(item, dict) for item in elements):
        raise UnixFormattingError(
            "Formatter cannot handle arrays which mix JSON objects "
            "with other datatypes."
        )

    elif any(isinstance(item, list) for item in elements):
        yield from emit_list_containing_lists(
            elements,  # type: ignore[arg-type]
            identifier=identifier,
        )
    else:
        yield from emit_scalar_list(
            elements,  # type: ignore[arg-type]
            identifier=identifier,
        )


def emit_scalar_list(
    elements: list[Scalar], identifier: str | None = None
) -> t.Iterator[str]:
    """
    Emit a list of scalars, with or without an identifier.

    Given an identifier, each element is placed on a separate line of output:

        >>> emit_scalar_list([1, 2], identifier="FOO")
        FOO\t1
        FOO\t2

    Without an identifier, all elements are placed on the same line:

        >>> emit_scalar_list([1, 2], identifier="FOO")
        1\t2
    """
    if identifier is not None:
        for item in elements:
            yield f"{identifier}\t{item}"
    else:
        yield "\t".join(str(item) for item in elements)


def emit_list_containing_lists(
    elements: list[Scalar | list[Scalar | NonScalar]],
    identifier: str | None = None,
) -> t.Iterator[str]:
    """
    Emit a list which contains nested lists, potentially mixed with scalars.
    First, the scalars are split off and emitted, then all of the nested lists are
    emitted in order of appearance.
    """
    scalars: list[Scalar] = []
    nested: list[list[Scalar | NonScalar]] = []
    for item in elements:
        if isinstance(item, list):
            nested.append(item)
        else:
            scalars.append(item)

    if scalars:
        yield from emit_scalar_list(scalars)
    for nested_list in nested:
        yield from emit_list(nested_list, identifier=identifier)


def emit_list_of_dicts(
    elements: list[dict[str, Scalar | NonScalar]], identifier: str | None = None
) -> t.Iterator[str]:
    keys = extract_scalar_keys(elements)
    for item in elements:
        yield from emit_dict(item, identifier=identifier, scalar_keys=keys)


def emit_dict(
    item: dict[str, Scalar | NonScalar],
    identifier: str | None = None,
    scalar_keys: list[str] | None = None,
) -> t.Iterator[str]:
    if scalar_keys is None:
        scalar_keys = extract_scalar_keys(item)
    scalars, non_scalars = partition_dict(item, scalar_keys)

    if scalars:
        if identifier is not None:
            yield identifier
        yield "\t".join(str(s) for s in scalars)

    for subkey, value in non_scalars:
        if isinstance(value, list):
            yield from emit_list(value, identifier=subkey.upper())
        else:
            yield from emit_dict(value, identifier=subkey.upper())


def partition_dict(
    item: dict[str, Scalar | NonScalar], scalar_keys: list[str]
) -> tuple[list[Scalar], list[tuple[str, NonScalar]]]:
    """
    Given a dict and a collection of keys for its scalar parts, split it into two lists
    representing the scalar and non-scalar parts.
    The non-scalar parts retain their keys.

    This method assumes that the 'scalar_keys' provided are correct to the dict in
    question.
    """
    scalars: list[Scalar] = []
    non_scalars: list[tuple[str, NonScalar]] = []

    non_scalar_keys = sorted(set(item.keys()) - set(scalar_keys))

    for key in scalar_keys:
        # NOTE:
        # the previous implementation used `.get(key, "")`, meaning
        # that in this very specific case, it converted a missing element to the empty
        # string rather than None -- this is considered a bug which we are fixing in
        # the new implementation
        value = item.get(key)

        # we are not guaranteed that the scalar keys really map to scalars
        # but if they don't, formatting will break, so error early
        if isinstance(value, (list, dict)):
            raise UnixFormattingError(
                "Error during UNIX formatting of response data. "
                "Lists where key-value mappings are not uniformly scalar or non-scalar "
                "are not supported."
            )

        scalars.append(str(value))

    for key in non_scalar_keys:
        value = item[key]

        # converse of the above: we are not "guaranteed" that the non-scalar keys
        # do not map to scalars on a heterogeneous list[dict] structure
        #
        # in practice, this is not reachable because `extract_scalar_keys()` prefers
        # to categorize data as scalar
        if not isinstance(value, (list, dict)):
            raise UnixFormattingError(
                "Error during UNIX formatting of response data. "
                "Lists where key-value mappings are not uniformly scalar or non-scalar "
                "are not supported."
            )

        non_scalars.append((key, value))

    return scalars, non_scalars


def extract_scalar_keys(
    element_or_elements: (
        dict[str, Scalar | NonScalar] | list[dict[str, Scalar | NonScalar]]
    ),
) -> list[str]:
    if isinstance(element_or_elements, dict):
        elements: list[dict[str, Scalar | NonScalar]] = [element_or_elements]
    else:
        elements = element_or_elements

    seen: set[str] = set()
    for key, value in chain(*(item.items() for item in elements)):
        if key in seen:
            continue
        if isinstance(value, (dict, list)):
            continue
        seen.add(key)
    return sorted(seen)
