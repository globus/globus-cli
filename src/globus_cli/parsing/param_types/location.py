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
        return str

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> t.Any:
        match_result = re.match(r"^([^,]+),([^,]+)$", value)
        if not match_result:
            self.fail(
                f"location '{value}' does not match the expected "
                "'latitude,longitude' format"
            )

        maybe_lat = match_result.group(1)
        maybe_lon = match_result.group(2)

        try:
            float(maybe_lat)
            float(maybe_lon)
        except ValueError:
            self.fail(
                f"location '{value}' is not a well-formed 'latitude,longitude' pair"
            )
        else:
            return f"{maybe_lat},{maybe_lon}"
