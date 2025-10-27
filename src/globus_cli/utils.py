from __future__ import annotations

import typing as t
import uuid

import click
import globus_sdk

from globus_cli.types import AnyCallable

if t.TYPE_CHECKING:
    # NB: GARE parsing requires other SDK components and therefore needs to be deferred
    # to avoid the performance impact of non-lazy imports
    from globus_sdk.gare import GARE

    from globus_cli.services.auth import CustomAuthClient

F = t.TypeVar("F", bound=AnyCallable)


def str2bool(v: str) -> bool | None:
    v = v.lower()
    if v in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif v in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        return None


def make_dict_json_serializable(data: dict[str, t.Any]) -> dict[str, t.Any]:
    return {
        k: _make_json_serializable(v)
        for k, v in data.items()
        if v is not globus_sdk.MISSING
    }


def _make_json_serializable(data: t.Any) -> t.Any:
    if isinstance(data, list):
        return [
            _make_json_serializable(item)
            for item in data
            if item is not globus_sdk.MISSING
        ]
    elif isinstance(data, dict):
        return {
            k: _make_json_serializable(v)
            for k, v in data.items()
            if v is not globus_sdk.MISSING
        }
    elif isinstance(data, uuid.UUID):
        return str(data)
    else:
        return data


def unquote_cmdprompt_single_quotes(arg: str) -> str:
    """
    remove leading and trailing single quotes from a string when
    there is a leading and trailing single quote

    per the name of this function, it is meant to provide compatibility
    with cmdprompt which interprets inputs like

        $ mycmd 'foo'

    as including the single quote chars and passes "'foo'" to our
    commands
    """
    if len(arg) >= 2 and arg[0] == "'" and arg[-1] == "'":
        return arg[1:-1]
    return arg


def fold_decorators(f: F, decorators: list[t.Callable[[F], F]]) -> F:
    for deco in decorators:
        f = deco(f)
    return f


def get_current_option_help(
    *, filter_names: t.Iterable[str] | None = None
) -> list[str]:
    ctx = click.get_current_context()
    cmd = ctx.command
    opts = [x for x in cmd.params if isinstance(x, click.Option)]
    if filter_names is not None:
        opts = [o for o in opts if o.name is not None and o.name in filter_names]
    return [o.get_error_hint(ctx) for o in opts]


def supported_parameters(c: AnyCallable) -> list[str]:
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


# wrap to add a `has_next()` method and `limit` param to a naive iterator
class PagingWrapper:
    def __init__(
        self,
        iterator: t.Iterator[t.Any],
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

    def __iter__(self) -> t.Iterator[t.Any]:
        yielded = 0
        while self.has_next() and (self.limit is None or yielded < self.limit):
            cur = self.next
            self._step()
            yield cur
            yielded += 1

    @property
    def json_converter(
        self,
    ) -> t.Callable[[t.Iterator[t.Any]], dict[str, list[t.Any]]]:
        if self.json_conversion_key is None:
            raise NotImplementedError("does not support json_converter")
        key: str = self.json_conversion_key

        def converter(it: t.Iterator[t.Any]) -> dict[str, list[t.Any]]:
            return {key: list(it)}

        return converter


def shlex_process_stream(
    process_command: click.Command, stream: t.TextIO, name: str
) -> None:
    """
    Use shlex to process stdin line-by-line.
    Also prints help text.

    Requires that @process_command be a Click command object, used for
    processing single lines of input. helptext is prepended to the standard
    message printed to interactive sessions.
    """
    import shlex

    for lineno, line in enumerate(stream.read().splitlines()):
        # get the argument vector:
        # do a shlex split to handle quoted paths with spaces in them
        # also lets us have comments with #
        argv = shlex.split(line, comments=True)
        if argv:
            try:
                with process_command.make_context(f"<process {name}>", argv) as ctx:
                    process_command.invoke(ctx)
            except click.ClickException as error:
                click.echo(
                    f"error encountered processing '{name}' in "
                    f"{stream.name} at line {lineno}:",
                    err=True,
                )
                click.echo(
                    click.style(f"  {error.format_message()}", fg="yellow"), err=True
                )
                click.get_current_context().exit(2)


class CLIAuthRequirementsError(Exception):
    """
    A class for internally generated auth requirements
    """

    def __init__(
        self,
        message: str,
        *,
        gare: GARE | None = None,
        epilog: str | None = None,
        origin: Exception | None = None,
    ) -> None:
        self.message = message
        self.epilog = epilog
        self.gare = gare
        self.origin = origin


def resolve_principal_urn(
    auth_client: CustomAuthClient,
    principal_type: t.Literal["identity", "group"] | None,
    principal: str,
    principal_type_key: str = "--principal-type",
) -> str:
    """
    Given a principal type and principal, resolve the principal into a URN.

    `principal` is expected to be one of:
      1. A UUID - in which case it is resolved to an identity or group dependent on
         the provided `principal_type` (default: "identity")
      2. A URN - in which case its prefix is validated if a `principal_type` is provided
      3. A username - in which case it is resolved to an identity urn (retrieving the
         UUID from a network call to auth)

    :param auth_client: An CustomAuthClient instance for resolving identities
    :param principal_type: The type of principal ("identity" or "group") this principal
        should be resolved as. Depending on the value of `principal`, this may be used
        for formatting or validating the provided principal string.
    :param principal: The principal to resolve (either a UUID, URN, or username)
    :param principal_type_key: Click parameter key to be used in principal_type click
        errors
    :return: A resolved principal URN string
    :raises click.UsageError: If the provided `principal` is incompatible with the
        provided `principal_type`
    """

    # Unspecified principal type
    if principal_type is None:
        if principal.startswith("urn:globus:auth:identity:") or principal.startswith(
            "urn:globus:groups:id:"
        ):
            return principal

        resolved = auth_client.maybe_lookup_identity_id(principal)
        if resolved:
            return f"urn:globus:auth:identity:{resolved}"

        raise click.UsageError(
            f"'{principal_type_key}' was unspecified and '{principal}' was not "
            "resolvable to a globus identity."
        )

    # Identity principal type
    elif principal_type == "identity":
        if principal.startswith("urn:globus:auth:identity:"):
            return principal

        if not principal.startswith("urn:"):
            resolved = auth_client.maybe_lookup_identity_id(principal)
            if resolved:
                return f"urn:globus:auth:identity:{resolved}"

        raise click.UsageError(
            f"'{principal_type_key} identity' but '{principal}' is not a valid "
            "username, identity UUID, or identity URN"
        )

    # Group principal type
    elif principal_type == "group":
        if principal.startswith("urn:globus:groups:id:"):
            return principal

        resolved = principal if _is_uuid(principal) else None
        if resolved:
            return f"urn:globus:groups:id:{resolved}"

        raise click.UsageError(
            f"'{principal_type_key} group' but '{principal}' is not a valid group UUID "
            "or URN"
        )

    # Unrecognized principal type
    else:
        raise NotImplementedError("unrecognized principal_type")


def _is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False
