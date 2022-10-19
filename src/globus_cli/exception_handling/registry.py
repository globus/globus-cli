from __future__ import annotations

import functools
import typing as t

import click
import globus_sdk

from globus_cli.parsing.command_state import CommandState

E = t.TypeVar("E", bound=Exception)

HOOK_TYPE = t.Callable[[E], t.NoReturn]
# something which can be decorated to become a hook
_HOOK_SRC_TYPE = t.Callable[[E], None]
CONDITION_TYPE = t.Callable[[E], bool]

# must cast the registry to avoid type errors around t.List[<nothing>]
_HOOKLIST_TYPE = t.List[
    t.Tuple[HOOK_TYPE, t.Union[str, t.Type[Exception]], CONDITION_TYPE]
]
_REGISTERED_HOOKS: _HOOKLIST_TYPE = t.cast(_HOOKLIST_TYPE, [])


def error_handler(
    *, error_class=None, condition=None, exit_status: int = 1
) -> t.Callable[[_HOOK_SRC_TYPE], HOOK_TYPE]:
    """decorator for excepthooks

    register each one, in order, with any relevant "condition"
    """

    def inner_decorator(fn):
        @functools.wraps(fn)
        def wrapped(exception):
            fn(exception)
            ctx = click.get_current_context()
            if isinstance(exception, globus_sdk.GlobusAPIError):
                # get the mapping by looking up the state and getting the mapping attr
                mapping = ctx.ensure_object(CommandState).http_status_map

                # if there is a mapped exit code, exit with that. Otherwise, exit below
                if exception.http_status in mapping:
                    ctx.exit(mapping[exception.http_status])
            ctx.exit(exit_status)

        _REGISTERED_HOOKS.append((wrapped, error_class, condition))
        return wrapped

    return inner_decorator


def find_handler(exception: Exception) -> HOOK_TYPE | None:
    for handler, error_class, condition in _REGISTERED_HOOKS:
        if isinstance(error_class, str):
            error_class_: type[Exception] = getattr(globus_sdk, error_class)
            assert issubclass(error_class_, Exception)
        else:
            error_class_ = error_class

        if error_class_ is not None and not isinstance(exception, error_class_):
            continue
        if condition is not None and not condition(exception):
            continue
        return handler
    return None
