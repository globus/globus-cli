from __future__ import annotations

from urllib.parse import urlparse

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType


class StringOrNull(click.ParamType):
    """
    Very similar to a basic string type, but one in which the empty string will
    be converted into an EXPLICIT_NULL
    """

    def get_metavar(self, param: click.Parameter) -> str:
        return "TEXT"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> str | ExplicitNullType:
        if value == "":
            return EXPLICIT_NULL
        else:
            return value


class UrlOrNull(StringOrNull):
    """
    Very similar to StringOrNull, but validates that the string is parsable as an
    http or https URL.
    """

    def get_metavar(self, param: click.Parameter) -> str:
        return "TEXT"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> str | ExplicitNullType:
        if value == "":
            return EXPLICIT_NULL
        else:
            try:
                url = urlparse(value)
                assert url[0] in ["http", "https"]
            except Exception:
                raise click.UsageError(
                    f"'{value}' is not a well-formed http or https URL"
                )
            return value


class IntOrNull(click.ParamType):
    """
    Very similar to a basic int type, but one in which the empty string will
    be converted into an EXPLICIT_NULL
    """

    def get_metavar(self, param: click.Parameter) -> str:
        return "[INT|null]"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> int | ExplicitNullType:
        if value == "null":
            return EXPLICIT_NULL
        else:
            try:
                return int(value)
            except ValueError:
                self.fail(
                    f'{value} is not a valid integer or the string "null"', param, ctx
                )
