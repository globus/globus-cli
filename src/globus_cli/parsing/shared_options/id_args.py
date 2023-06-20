"""
These are semi-standard arg names with overridable metavars.

Basic usage:

>>> @endpoint_id_arg
>>> def command_func(endpoint_id: uuid.UUID):
>>>     ...

Override metavar (note that argname is unchanged):

>>> @endpoint_id_arg(metavar='HOST_ENDPOINT_ID')
>>> def command_func(endpoint_id: uuid.UUID):
>>>     ...
"""
from __future__ import annotations

import functools
import typing as t

import click


def collection_id_arg(f: t.Callable | None = None, *, metavar: str = "COLLECTION_ID"):
    if f is None:
        return functools.partial(collection_id_arg, metavar=metavar)
    return click.argument("collection_id", metavar=metavar, type=click.UUID)(f)


def endpoint_id_arg(f: t.Callable | None = None, *, metavar: str = "ENDPOINT_ID"):
    if f is None:
        return functools.partial(endpoint_id_arg, metavar=metavar)
    return click.argument("endpoint_id", metavar=metavar, type=click.UUID)(f)


def flow_id_arg(f: t.Callable | None = None, *, metavar: str = "FLOW_ID"):
    if f is None:
        return functools.partial(flow_id_arg, metavar=metavar)
    return click.argument("flow_id", metavar=metavar, type=click.UUID)(f)


def run_id_arg(f: t.Callable | None = None, *, metavar: str = "RUN_ID"):
    if f is None:
        return functools.partial(run_id_arg, metavar=metavar)
    return click.argument("run_id", metavar=metavar, type=click.UUID)(f)
