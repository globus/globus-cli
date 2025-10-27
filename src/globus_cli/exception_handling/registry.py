from __future__ import annotations

import dataclasses
import functools
import typing as t

import click
import globus_sdk

from globus_cli.parsing.command_state import CommandState
from globus_cli.utils import CLIAuthRequirementsError

E = t.TypeVar("E", bound=Exception)
E_Globus = t.TypeVar("E_Globus", bound="globus_sdk.GlobusAPIError")

HOOK_TYPE = t.Callable[[E], t.NoReturn]
# something which can be decorated to become a hook
_HOOK_SRC_TYPE = t.Union[t.Callable[[E], None], t.Callable[[E], t.Optional[int]]]

CONDITION_TYPE = t.Callable[[E], bool]

_REGISTERED_HOOKS: list[DeclaredHook[t.Any]] = []


@dataclasses.dataclass
class DeclaredHook(t.Generic[E]):
    hook_func: HOOK_TYPE[E]
    condition: CONDITION_TYPE[E]


def register_hook(hook: DeclaredHook[t.Any]) -> None:
    _REGISTERED_HOOKS.append(hook)


def sdk_error_handler(
    *,
    error_class: str = "GlobusAPIError",
    condition: t.Callable[[E_Globus], bool] | None = None,
    exit_status: int = 1,
) -> t.Callable[[_HOOK_SRC_TYPE[E_Globus]], DeclaredHook[E_Globus]]:
    return _error_handler(
        condition=_build_condition(condition, error_class), exit_status=exit_status
    )


def error_handler(
    *,
    error_class: type[E],
    exit_status: int = 1,
) -> t.Callable[[_HOOK_SRC_TYPE[E]], DeclaredHook[E]]:
    return _error_handler(
        condition=_build_condition(None, error_class), exit_status=exit_status
    )


def invoke_exception_handler(exception: Exception) -> None:
    """
    Find and invoke a registered exception handler for the given exception.

    The first handler with a matching condition for either the exception or the
    origin exception (if applicable) is invoked and no further handlers are checked.

    Has no effect if no handlers match.
    """

    for hook in _REGISTERED_HOOKS:
        if hook.condition(exception):
            hook.hook_func(exception)

        elif isinstance(exception, CLIAuthRequirementsError):
            # Special case the CLIAuthRequirementsError to allow hooks to
            # match on the original, unmodified, exception.
            if exception.origin and hook.condition(exception.origin):
                hook.hook_func(exception.origin)


def _error_handler(
    *,
    condition: t.Callable[[E], bool],
    exit_status: int = 1,
) -> t.Callable[[_HOOK_SRC_TYPE[E]], DeclaredHook[E]]:
    """
    Decorator for excepthooks, converting the hook functions into
    declared hook objects.
    """

    def inner_decorator(fn: _HOOK_SRC_TYPE[E]) -> DeclaredHook[E]:
        @functools.wraps(fn)
        def wrapped(exception: E) -> t.NoReturn:
            hook_result = fn(exception)
            ctx = click.get_current_context()

            if isinstance(exception, globus_sdk.GlobusAPIError):
                # get the mapping by looking up the state and getting the mapping attr
                mapping = ctx.ensure_object(CommandState).http_status_map

                # if there is a mapped exit code, exit with that. Otherwise, exit below
                if exception.http_status in mapping:
                    ctx.exit(mapping[exception.http_status])

            # if the hook instructed that a specific error code be used, use that
            if hook_result is not None:
                ctx.exit(hook_result)

            ctx.exit(exit_status)

        return DeclaredHook(wrapped, condition)

    return inner_decorator


@t.overload
def _build_condition(
    condition: CONDITION_TYPE[E],
    error_class: str | None,
) -> CONDITION_TYPE[E]: ...


@t.overload
def _build_condition(
    condition: CONDITION_TYPE[E], error_class: type[E]
) -> CONDITION_TYPE[E]: ...


@t.overload
def _build_condition(condition: None, error_class: type[E]) -> CONDITION_TYPE[E]: ...


@t.overload
def _build_condition(
    condition: None, error_class: str | None
) -> CONDITION_TYPE[t.Any]: ...


def _build_condition(
    condition: CONDITION_TYPE[E] | None, error_class: str | type[E] | None
) -> CONDITION_TYPE[E]:
    inner_condition: CONDITION_TYPE[E]

    if condition is None:
        if error_class is None:
            raise ValueError("a hook must specify either condition or error_class")

        def inner_condition(exception: Exception) -> bool:
            error_class_ = _resolve_error_class(error_class)
            return isinstance(exception, error_class_)

    elif error_class is None:
        inner_condition = condition

    else:

        def inner_condition(exception: Exception) -> bool:
            error_class_ = _resolve_error_class(error_class)
            return isinstance(exception, error_class_) and condition(exception)

    return inner_condition


def _resolve_error_class(error_class: str | type[E]) -> type[E]:
    if isinstance(error_class, str):
        resolved = getattr(globus_sdk, error_class, None)
        if resolved is None:
            raise LookupError(f"no such globus_sdk error class '{error_class}'")
        if not (isinstance(resolved, type) and issubclass(resolved, Exception)):
            raise ValueError(f"'globus_sdk.{error_class}' is not an error class")
        return resolved  # type: ignore[return-value]
    else:
        return error_class
