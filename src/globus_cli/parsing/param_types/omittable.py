from __future__ import annotations

import datetime
import typing as t
import uuid

import click.types
import globus_sdk

from globus_cli._click_compat import (
    OLDER_CLICK_API,
    shim_get_metavar,
    shim_get_missing_message,
)

if t.TYPE_CHECKING:
    _OmittableIntBase = click.ParamType[int | globus_sdk.MissingType]
    _OmittableStrBase = click.ParamType[str | globus_sdk.MissingType]
    _OmittableUUIDBase = click.ParamType[uuid.UUID | globus_sdk.MissingType]
    _OmittableDateTimeBase = click.ParamType[datetime.datetime | globus_sdk.MissingType]
else:
    _OmittableIntBase = click.ParamType
    _OmittableStrBase = click.ParamType
    _OmittableUUIDBase = click.ParamType
    _OmittableDateTimeBase = click.DateTime


class OmittableInt(_OmittableIntBase):
    name = "integer"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> int | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return click.INT.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[int, globus_sdk.MissingType]  # type: ignore[return-value]


class OmittableString(_OmittableStrBase):
    name = "text"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> str | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return click.STRING.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[str, globus_sdk.MissingType]  # type: ignore[return-value]


class OmittableUUID(_OmittableUUIDBase):
    name = "uuid"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> uuid.UUID | globus_sdk.MissingType:
        if value is globus_sdk.MISSING:
            return globus_sdk.MISSING
        return click.UUID.convert(value, param, ctx)

    def get_type_annotation(self, param: click.Parameter) -> type:
        return t.Union[uuid.UUID, globus_sdk.MissingType]  # type: ignore[return-value]


class OmittableChoice(_OmittableStrBase):
    name = "choice"

    def __init__(self, choices: t.Sequence[str], case_sensitive: bool = True) -> None:
        self._inner_choice = click.Choice(choices, case_sensitive=case_sensitive)

    @shim_get_metavar
    def get_metavar(self, param: click.Parameter, ctx: click.Context) -> str | None:
        if OLDER_CLICK_API:
            return self._inner_choice.get_metavar(param)  # type: ignore[call-arg]
        return self._inner_choice.get_metavar(param, ctx)

    @shim_get_missing_message
    def get_missing_message(
        self, param: click.Parameter, ctx: click.Context | None
    ) -> str | None:
        if OLDER_CLICK_API:
            return self._inner_choice.get_missing_message(  # type: ignore[call-arg]
                param
            )
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
