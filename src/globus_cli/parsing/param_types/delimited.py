from __future__ import annotations

import typing as t

import click
import globus_sdk

from globus_cli._click_compat import (
    OLDER_CLICK_API,
    shim_get_metavar,
    shim_get_missing_message,
)

if t.TYPE_CHECKING:
    from click.shell_completion import CompletionItem


class CommaDelimitedList(click.ParamType):
    def __init__(
        self,
        *,
        convert_values: t.Callable[[str], str] | None = None,
        choices: t.Iterable[str] | None = None,
        omittable: bool = False,
    ) -> None:
        super().__init__()
        self._omittable = omittable
        self.convert_values = convert_values
        self.choices = list(choices) if choices is not None else None

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str:
        if self.choices is not None:
            return "{" + ",".join(self.choices) + "}"
        return "TEXT,TEXT,..."

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> list[str] | globus_sdk.MissingType:
        if self._omittable and value is globus_sdk.MISSING:
            return globus_sdk.MISSING

        value = super().convert(value, param, ctx)

        # if `--foo` is a comma delimited list and someone passes
        # `--foo ""`, take that as `foo=[]` rather than foo=[""]
        #
        # the alternative is fine, but we have to choose one and this is
        # probably "closer to what the caller meant"
        #
        # it means that if you take
        # `--foo={",".join(original)}`, you will get a value equal to
        # `original` back if `original=[]` (but not if `original=[""]`)
        resolved = value.split(",") if value else []

        if self.convert_values is not None:
            resolved = [self.convert_values(x) for x in resolved]

        if self.choices is not None:
            bad_values = [x for x in resolved if x not in self.choices]
            if bad_values:
                self.fail(
                    f"the values {bad_values} were not valid choices",
                    param=param,
                    ctx=ctx,
                )

        return resolved

    def get_type_annotation(self, param: click.Parameter) -> type:
        if self._omittable:
            return t.Union[  # type: ignore[return-value]
                list[str], globus_sdk.MissingType
            ]
        return list[str]


class ColonDelimitedChoiceTuple(click.ParamType):
    """
    A colon-delimited choice type which wraps the existing click.Choice type.

    It accepts colon-separated options as its input, and uses the underlying
    choice type to implement behaviors amongst those options.
    As its output (`convert()`), it produces tuples, with the elements split on
    `:` characters.

    It uses the `get_type_annotation()` hook from `click-type-test` to indicate
    the exact literal type which should be used to annotate the parameter it
    passes.
    """

    name = "colon_delimited_choice"

    def __init__(
        self,
        *,
        choices: t.Sequence[str],
        case_sensitive: bool = True,
    ) -> None:
        super().__init__()
        self.inner_choice_param = click.Choice(choices, case_sensitive=case_sensitive)

        self.unpacked_choices = self._unpack_choices()

    def to_info_dict(self) -> dict[str, t.Any]:
        return self.inner_choice_param.to_info_dict()

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str | None:
        if OLDER_CLICK_API:
            # type checking on newer click versions will flag this, but incorrectly so
            return self.inner_choice_param.get_metavar(param)  # type: ignore[call-arg]
        return self.inner_choice_param.get_metavar(param, ctx)

    @shim_get_missing_message
    def get_missing_message(
        self, param: click.Parameter, ctx: click.Context | None
    ) -> str:
        if OLDER_CLICK_API:
            # type checking on newer click versions will flag this, but incorrectly so
            return self.inner_choice_param.get_missing_message(
                param=param  # type: ignore[call-arg]
            )
        return self.inner_choice_param.get_missing_message(param=param, ctx=ctx)

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> list[CompletionItem]:
        return self.inner_choice_param.shell_complete(ctx, param, incomplete)

    def _unpack_choices(self) -> list[tuple[str, ...]]:
        split_choices = [
            tuple(choice.split(":")) for choice in self.inner_choice_param.choices
        ]
        if len(split_choices) == 0:
            raise NotImplementedError("No choices")
        choice_len = len(split_choices[0])
        if any(len(choice) != choice_len for choice in split_choices):
            raise NotImplementedError("Not all choices have the same length")
        return split_choices

    def get_type_annotation(self, param: click.Parameter) -> type:
        # convert tuples of choices to a tuple of literals of choices
        #
        # the transformation is tricky, but it effectively does this:
        #     [(1, 3), (2, 4)] -> tuple[Literal[1, 2], Literal[3, 4]]

        # unzip/transpose using zip(*x)
        unzipped_choices = zip(*self.unpacked_choices)

        # each tuple of choices becomes a Literal
        literals = [t.Literal[choices] for choices in unzipped_choices]

        # runtime calls to __class_getitem__ require a single tuple argument
        # so we explicitly `tuple(...)` to get the right data shape
        # type-ignore because mypy complains about multiple errors due to
        # its misunderstanding of a runtime-only __class_getitem__ usage
        return tuple[tuple(literals)]  # type: ignore

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> tuple[str, ...]:
        return tuple(self.inner_choice_param.convert(value, param, ctx).split(":"))
