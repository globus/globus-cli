from __future__ import annotations

import typing as t

import click

from globus_cli.types import AnyCommand

C = t.TypeVar("C", bound=AnyCommand)


class OneUseOption(click.Option):
    """
    Overwrites the type_cast_value function inherited from click.Parameter
    to assert an option was only used once, and then converts it back
    to the original value type.
    """

    def __init__(
        self,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None:
        if "callback" in kwargs:
            raise ValueError(
                "Internal error. OneUseOption cannot be used with a callback function."
            )
        kwargs["callback"] = OneUseOption._conversion_callback
        super().__init__(*args, **kwargs)

    def has_explicit_annotation(self) -> bool:
        return True

    @property
    def type_annotation(self) -> type:
        from globus_cli.parsing.param_types import EndpointPlusPath

        if self.count:
            return bool

        if isinstance(self.type, EndpointPlusPath):
            return t.Union[self.type.get_type_annotation(self), None]  # type: ignore[return-value]  # noqa: E501

        raise NotImplementedError(
            "OneUseOption requires a type annotation in this case."
        )

    @classmethod
    def _conversion_callback(
        cls, ctx: click.Context, param: click.Parameter, value: t.Any
    ) -> t.Any:
        # if the option takes arguments (multiple was set to true)
        # assert no more than one argument was gotten, and if an argument
        # was gotten, take it out of the tuple and return it
        if param.multiple:
            if len(value) > 1:
                raise click.BadParameter("Option used multiple times.", ctx=ctx)
            if len(value):
                return value[0]
            else:
                return None

        # if the option was a flag (converted to a count) assert that the flag
        # count is no more than one, and type cast back to a bool
        elif isinstance(param, click.Option) and param.count:
            if value > 1:
                raise click.BadParameter("Option used multiple times.", ctx=ctx)
            return bool(value)

        else:
            raise ValueError(
                "Internal error, OneUseOption expected either "
                "multiple or count, but got neither."
            )


def one_use_option(*args: t.Any, **kwargs: t.Any) -> t.Callable[[C], C]:
    """
    Wrapper of the click.option decorator that replaces any instances of
    the Option class with the custom OneUseOption class
    """
    # cannot force a multiple or count option to be single use
    if "multiple" in kwargs or "count" in kwargs:
        raise ValueError(
            "Internal error, one_use_option cannot be used with multiple or count."
        )

    # cannot force a non Option Parameter (argument) to be a OneUseOption
    if kwargs.get("cls"):
        raise ValueError(
            "Internal error, one_use_option cannot overwrite "
            "cls {}.".format(kwargs.get("cls"))
        )

    # use our OneUseOption class instead of a normal Option
    kwargs["cls"] = OneUseOption

    # if dealing with a flag, switch to a counting option,
    # and then assert if the count is not greater than 1 and cast to a bool
    if kwargs.get("is_flag"):
        kwargs["is_flag"] = False  # mutually exclusive with count
        kwargs["count"] = True
    # if not a flag, this option takes an argument(s), switch to a multiple
    # option, assert the len is 1, and treat the first element as the value
    else:
        kwargs["multiple"] = True

    # decorate with the click.option decorator, but with our custom kwargs
    return click.option(*args, **kwargs)
