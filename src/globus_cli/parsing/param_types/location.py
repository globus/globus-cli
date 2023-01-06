from __future__ import annotations

import re
import typing as t

import click

from .annotated_param import AnnotatedParamType


class LocationType(AnnotatedParamType):
    """
    Validates that given location string is two comma separated floats
    """

    name = "LATITUDE,LONGITUDE"

    def get_type_annotation(self, param: click.Parameter) -> type:
        # mypy does not recognize this as a valid usage at runtime
        # ignore for now
        return tuple[float, float]  # type: ignore[no-any-return,misc]

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        try:
            match = re.match("^(.*),(.*)$", value)
            if not match:
                raise ValueError()
            float(match.group(1))
            float(match.group(2))
            return value
        except (ValueError, AttributeError):
            self.fail(
                f"location {value} is not two comma separated floats "
                "for latitude and longitude"
            )
