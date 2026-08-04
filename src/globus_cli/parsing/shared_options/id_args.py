"""
These are standardized arg names.

Basic usage:

>>> @endpoint_id_arg
>>> def command_func(endpoint_id: uuid.UUID):
>>>     ...
"""

import typing as t

import click

C = t.TypeVar("C", bound=t.Union[click.Command, t.Callable[..., t.Any]])


def collection_id_arg(f: C) -> C:
    return click.argument("collection_id", metavar="COLLECTION_ID", type=click.UUID)(f)


def endpoint_id_arg(f: C) -> C:
    return click.argument("endpoint_id", metavar="ENDPOINT_ID", type=click.UUID)(f)


def flow_id_arg(f: C) -> C:
    return click.argument("flow_id", metavar="FLOW_ID", type=click.UUID)(f)


def run_id_arg(f: C) -> C:
    return click.argument("run_id", metavar="RUN_ID", type=click.UUID)(f)


def web_input_id_arg(f: C) -> C:
    return click.argument("web_input_id", metavar="WEB_INPUT_ID", type=click.UUID)(f)
