from __future__ import annotations

import re
import typing as t

import click


class LocationType(click.ParamType[str]):
    """
    Validates that given location string is two comma separated floats
    """

    name = "LATITUDE,LONGITUDE"

    def convert(
        self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
    ) -> str:
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
