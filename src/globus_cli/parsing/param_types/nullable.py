from urllib.parse import urlparse

import click

from globus_cli.constants import EXPLICIT_NULL, ExplicitNullType

from .annotated_param import AnnotatedParamType


def nullable_multi_callback(null="null"):
    """
    A callback which converts multiple=True options as follows:
    - empty results, [] => None
    - [<null>,] => []
    - anything else => passthrough

    This makes the null value explicit, and not setting it results in omission, not
    clearing.

    The null value used here is tunable. If set to a non-string value when using a
    string type, like `None`, it means that "there is no null value" because
    there is no way to pass `[]`

    Note that this will see values after the type conversion has happened.
    """

    def callback(ctx, param, value):
        if value is None or len(value) == 0:
            return None
        if len(value) == 1 and value[0] == null:
            return []
        return value

    return callback


class StringOrNull(AnnotatedParamType):
    """
    Very similar to a basic string type, but one in which the empty string will
    be converted into an EXPLICIT_NULL
    """

    def get_type_annotation(self, param: click.Parameter) -> type:
        return str | ExplicitNullType

    def get_metavar(self, param):
        return "TEXT"

    def convert(self, value, param, ctx):
        if value is None:
            return None
        elif value == "":
            return EXPLICIT_NULL
        else:
            return value


class UrlOrNull(StringOrNull):
    """
    Very similar to StringOrNull, but validates that the string is parsable as an
    http or https URL.
    """

    def get_metavar(self, param):
        return "TEXT"

    def convert(self, value, param, ctx):
        if value is None:
            return None
        elif value == "":
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
