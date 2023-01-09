from __future__ import annotations

import typing as t

import click

C = t.TypeVar("C", bound=t.Union[click.BaseCommand, t.Callable])


class _Sentinel:
    pass


_SENTINEL = _Sentinel()


class AnnotatedOption(click.Option):
    def __init__(
        self,
        *args: t.Any,
        type_annotation: type | _Sentinel = _SENTINEL,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._type_annotation = type_annotation

    def has_explicit_annotation(self) -> bool:
        if self._type_annotation == _SENTINEL:
            return False
        return True

    @property
    def type_annotation(self) -> type:
        if self._type_annotation == _SENTINEL:
            raise ValueError("cannot get annotation from option when it is not set")

        return t.cast(type, self._type_annotation)


class OneUseOption(AnnotatedOption):
    """
    Overwrites the type_cast_value function inherited from click.Parameter
    to assert an option was only used once, and then converts it back
    to the original value type.
    """

    def type_cast_value(self, ctx: click.Context, value: t.Any) -> t.Any:

        # get the result of a normal type_cast
        converted_val = super().type_cast_value(ctx, value)

        # if the option takes arguments (multiple was set to true)
        # assert no more than one argument was gotten, and if an argument
        # was gotten, take it out of the tuple and return it
        if self.multiple:
            if len(converted_val) > 1:
                raise click.BadParameter("Option used multiple times.", ctx=ctx)
            if len(converted_val):
                return converted_val[0]
            else:
                return None

        # if the option was a flag (converted to a count) assert that the flag
        # count is no more than one, and type cast back to a bool
        elif self.count:
            if converted_val > 1:
                raise click.BadParameter("Option used multiple times.", ctx=ctx)
            return bool(converted_val)

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

    # cannot force a non Option Paramater (argument) to be a OneUseOption
    if kwargs.get("cls"):
        raise TypeError(
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
        if "type_annotation" not in kwargs:
            kwargs["type_annotation"] = bool

    # if not a flag, this option takes an argument(s), switch to a multiple
    # option, assert the len is 1, and treat the first element as the value
    else:
        kwargs["multiple"] = True

    # decorate with the click.option decorator, but with our custom kwargs
    return click.option(*args, **kwargs)
