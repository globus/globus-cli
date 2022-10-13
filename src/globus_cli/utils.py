from __future__ import annotations

import json
from typing import Any, Callable, Iterable, Iterator, TextIO, cast

import click

from globus_cli.types import DATA_CONTAINER_T, FIELD_LIST_T


def get_current_option_help(*, filter_names: Iterable[str] | None = None) -> list[str]:
    ctx = click.get_current_context()
    cmd = ctx.command
    opts = [x for x in cmd.params if isinstance(x, click.Option)]
    if filter_names is not None:
        opts = [o for o in opts if o.name is not None and o.name in filter_names]
    return [o.get_error_hint(ctx) for o in opts]


def supported_parameters(c: Callable) -> list[str]:
    import inspect

    sig = inspect.signature(c)
    return list(sig.parameters.keys())


def format_list_of_words(first: str, *rest: str) -> str:
    if not rest:
        return first
    if len(rest) == 1:
        return f"{first} and {rest[0]}"
    return ", ".join([first] + list(rest[:-1])) + f", and {rest[-1]}"


def format_plural_str(
    formatstr: str, pluralizable: dict[str, str], use_plural: bool
) -> str:
    """
    Format text with singular or plural forms of words. Use the singular forms as
    keys in the format string.

    Usage:

    >>> command_list = [...]
    >>> fmtstr = "you need to run {this} {command}:"
    >>> print(
    ...     format_plural_str(
    ...         fmtstr,
    ...         {"this": "these", "command": "commands"},
    ...         len(command_list) == 1
    ...     )
    ... )
    >>> print("  " + "\n  ".join(command_list))
    """
    argdict = {
        singular: plural if use_plural else singular
        for singular, plural in pluralizable.items()
    }
    return formatstr.format(**argdict)


class _FuncWithFilterKey:
    _filter_key: str


def sorted_json_field(
    key: str,
) -> Callable[[DATA_CONTAINER_T], str]:
    """Define sorted JSON output for text output containing complex types."""

    def field_func(data: DATA_CONTAINER_T) -> str:
        return json.dumps(data[key], sort_keys=True)

    ret = cast(_FuncWithFilterKey, field_func)
    ret._filter_key = key
    return field_func


def filter_fields(
    check_fields: FIELD_LIST_T,
    container: DATA_CONTAINER_T,
) -> FIELD_LIST_T:
    """
    Given a set of fields, this is a list of fields actually found in some containing
    object.

    Always includes keyfunc fields unless they set the magic _filter_key attribute
    sorted_json_field above is a good example of doing this
    """
    fields: FIELD_LIST_T = []
    for field_to_check in check_fields:
        # FormatField objects get included always
        if not isinstance(field_to_check, tuple):
            fields.append(field_to_check)
            continue

        name, key = field_to_check
        check_key = key
        if callable(key) and hasattr(key, "_filter_key"):
            check_key = cast(_FuncWithFilterKey, key)._filter_key

        # if it's a string lookup, check if it's contained (and skip if not)
        if isinstance(check_key, str):
            subkeys = check_key.split(".")
            skip_subkey = False

            check_container = container
            for check_subkey in subkeys[:-1]:
                if check_subkey not in check_container:
                    skip_subkey = True
                    break
                check_container = check_container[check_subkey]
            if skip_subkey or subkeys[-1] not in check_container:
                continue

        # anything else falls through to success
        # includes keyfuncs which don't set _filter_key
        fields.append((name, key))
    return fields


class CLIStubResponse:
    """
    A stub response class to make arbitrary data accessible in a way similar to a
    GlobusHTTPResponse object.
    """

    def __init__(self, data: DATA_CONTAINER_T) -> None:
        self.data = data

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __getitem__(self, key: str) -> Any:
        return self.data[key]


# wrap to add a `has_next()` method and `limit` param to a naive iterator
class PagingWrapper:
    def __init__(
        self,
        iterator: Iterator[Any],
        limit: int | None = None,
        json_conversion_key: str | None = None,
    ) -> None:
        self.iterator = iterator
        self.next = None
        self.limit = limit
        self.json_conversion_key = json_conversion_key
        self._step()

    def _step(self) -> None:
        try:
            self.next = next(self.iterator)
        except StopIteration:
            self.next = None

    def has_next(self) -> bool:
        return self.next is not None

    def __iter__(self) -> Iterator[Any]:
        yielded = 0
        while self.has_next() and (self.limit is None or yielded < self.limit):
            cur = self.next
            self._step()
            yield cur
            yielded += 1

    @property
    def json_converter(self) -> Callable[[Iterator[Any]], dict[str, list[Any]]]:
        if self.json_conversion_key is None:
            raise NotImplementedError("does not support json_converter")
        key: str = self.json_conversion_key

        def converter(it: Iterator[Any]) -> dict[str, list[Any]]:
            return {key: list(it)}

        return converter


def shlex_process_stream(process_command: click.Command, stream: TextIO) -> None:
    """
    Use shlex to process stdin line-by-line.
    Also prints help text.

    Requires that @process_command be a Click command object, used for
    processing single lines of input. helptext is prepended to the standard
    message printed to interactive sessions.
    """
    import shlex

    # use readlines() rather than implicit file read line looping to force
    # python to properly capture EOF (otherwise, EOF acts as a flush and
    # things get weird)
    for line in stream.readlines():
        # get the argument vector:
        # do a shlex split to handle quoted paths with spaces in them
        # also lets us have comments with #
        argv = shlex.split(line, comments=True)
        if argv:
            try:
                process_command.main(args=argv)
            except SystemExit as e:
                if e.code != 0:
                    raise
