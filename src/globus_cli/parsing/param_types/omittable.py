from __future__ import annotations

import datetime
import typing as t
import uuid

import click.types
import globus_sdk


class OmittableInt(click.ParamType[int | globus_sdk.MissingType]):
    name = "integer"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> int | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return click.INT.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[int, globus_sdk.MissingType]  # type: ignore[return-value]


class OmittableString(click.ParamType[str | globus_sdk.MissingType]):
    name = "text"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> str | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return click.STRING.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[str, globus_sdk.MissingType]  # type: ignore[return-value]


class OmittableUUID(click.ParamType[uuid.UUID | globus_sdk.MissingType]):
    name = "uuid"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return click.UUID.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[uuid.UUID, globus_sdk.MissingType]  # type: ignore[return-value]


class OmittableChoice(click.ParamType[str | globus_sdk.MissingType]):
    name = "choice"

    def __init__(self, choices: t.Sequence[str], case_sensitive: bool = True) -> None:
        self._inner_choice = click.Choice(choices, case_sensitive=case_sensitive)

    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str | None:
        return self._inner_choice.get_metavar(param, ctx)

    def get_missing_message(
        self, param: click.Parameter, ctx: click.Context | None
    ) -> str | None:
        return self._inner_choice.get_missing_message(param, ctx)

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> str | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return self._inner_choice.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        literal = t.Literal[  # type: ignore[valid-type]
            tuple(self._inner_choice.choices)
        ]
        return t.Union[literal, globus_sdk.MissingType]  # type: ignore[return-value]


# The converted type of a ParamType is signified by its type parameter, but we want to
# inherit the runtime behavior of DateTime, which defines this as `datetime.datetime`.
# To make type checking accurate but inherit behavior at runtime, define the base class
# differently at runtime vs type-checking-time.
if t.TYPE_CHECKING:
    _OmittableDateTimeBase = click.ParamType[datetime.datetime | globus_sdk.MissingType]
else:
    _OmittableDateTimeBase = click.DateTime


class OmittableDateTime(_OmittableDateTimeBase):
    name = "datetime"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> datetime.datetime | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return super().convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[  # type: ignore[return-value]
            datetime.datetime, globus_sdk.MissingType
        ]


OMITTABLE_INT = OmittableInt()
OMITTABLE_STRING = OmittableString()
OMITTABLE_UUID = OmittableUUID()
