from __future__ import annotations

import typing as t

import click

from .annotated_param import AnnotatedParamType


class CommaDelimitedList(AnnotatedParamType):
    def __init__(
        self,
        *,
        convert_values: t.Callable[[str], str] | None = None,
        choices: t.Iterable[str] | None = None,
    ):
        super().__init__()
        self.convert_values = convert_values
        self.choices = list(choices) if choices is not None else None

    def get_type_annotation(self, param: click.Parameter) -> type:
        return list[str]

    def get_metavar(self, param):
        if self.choices is not None:
            return "{" + ",".join(self.choices) + "}"
        return "TEXT,TEXT,..."

    def convert(self, value, param, ctx):
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
