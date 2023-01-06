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
        return tuple[float, float]

    def convert(self, value: t.Any, param: click.Parameter, ctx: click.Context):
        try:
            match = re.match("^(.*),(.*)$", value)
            float(match.group(1))
            float(match.group(2))
            return value
        except (ValueError, AttributeError):
            self.fail(
                f"location {value} is not two comma separated floats "
                "for latitude and longitude"
            )
