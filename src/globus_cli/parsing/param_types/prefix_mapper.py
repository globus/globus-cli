from __future__ import annotations

import json

import click

from globus_cli.constants import EXPLICIT_NULL
from globus_cli.types import JsonValue

from .annotated_param import AnnotatedParamType


class StringPrefixMapper(AnnotatedParamType):
    """
    This is the base class for mapping types which try to split up inputs and parse them
    based on identifying prefixes

    It can be used to define a nice system for dispatch on prefixes
    """

    __prefix_mapping__: dict[str, str] = {}
    __prefix_metavars__: list[str] = []

    def __init__(self, *args, null=None, **kwargs):
        self.null = null
        super().__init__(*args, **kwargs)

    def get_metavar(self, param):
        return "[" + "|".join(self.__prefix_metavars__) + "]"

    def convert(self, value, param, ctx):
        if value is None:
            return None
        if self.null is not None and value == self.null:
            return EXPLICIT_NULL

        return self.prefix_mapper_parse_input(value)

    def _prefix_mapper_get_parser(self, parsername):
        return getattr(self, parsername)

    def prefix_mapper_default_parser(self, value):
        """override-able default (no-op)"""
        return value

    def prefix_mapper_parse_input(self, value):
        """
        Given an input, try to map it to a parsing func by prefix
        """
        for prefix, parser in self.__prefix_mapping__.items():
            if value.startswith(prefix):
                value = value[len(prefix) :]
                return self._prefix_mapper_get_parser(parser)(value)
        return self.prefix_mapper_default_parser(value)


class JSONStringOrFile(StringPrefixMapper):
    """
    This type parses a JSON string or falls back to loading JSON data from a
    path, specified by `file:PATH`

    Implements file: -> json
    Default is parse-as-JSON
    """

    __prefix_mapping__ = {"file:": "prefix_mapper_parse_json_file"}
    __prefix_metavars__ = ["JSON", "file:JSON_FILE"]

    def get_type_annotation(self, param: click.Parameter) -> type:
        return JsonValue

    def prefix_mapper_parse_json_file(self, value):
        try:
            with open(value) as fp:
                return json.load(fp)
        except json.JSONDecodeError:
            raise click.UsageError(f"{value} did not contain valid JSON")
        except FileNotFoundError:
            raise click.UsageError(f"FileNotFound: {value} does not exist")

    def prefix_mapper_default_parser(self, value):
        """
        The mapper also provides a shared JSON string parser which produces nice errors
        """
        # try to handle by parsing as JSON data
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            addendum = (
                ". Did you mean to use 'file:'?" if value.startswith("file") else ""
            )
            # did not match as a URI or parse as JSON, error
            raise click.UsageError(f"the string '{value}' is not valid JSON{addendum}")
