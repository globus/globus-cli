import typing as t

import click


def none_to_empty_dict(
    ctx: click.Context, param: click.Parameter, value: t.Any
) -> t.Any:
    """
    This is a "preset" callback which converts None to the empty dict

    It must exist in order to support the automatic type deduction tests, which inspect
    parameters and decide what types are passed to commands
    """
    if value is None:
        return {}
    return value
