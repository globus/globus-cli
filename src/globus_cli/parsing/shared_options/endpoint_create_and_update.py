from __future__ import annotations

import functools
from typing import Callable, TypeVar, Union, cast, overload

import click

C = TypeVar("C", bound=Union[Callable, click.Command])


@overload
def endpointish_create_options(f: C) -> C:
    ...


@overload
def endpointish_create_options(*, name: str) -> Callable[[C], C]:
    ...


def endpointish_create_options(
    f: C | None = None, *, name: str = "endpoint"
) -> Callable[[C], C] | C:
    if f is None:
        return cast(
            Callable[[C], C], functools.partial(endpointish_create_options, name=name)
        )
    f = click.option("--description", help=f"Description for the {name}")(f)
    f = click.option("--info-link", help=f"Link for Info about the {name}")(f)
    f = click.option("--contact-info", help=f"Contact Info for the {name}")(f)
    f = click.option("--contact-email", help=f"Contact Email for the {name}")(f)
    f = click.option("--organization", help=f"Organization for the {name}")(f)
    f = click.option("--department", help=f"Department which operates the {name}")(f)
    f = click.option(
        "--keywords",
        help=f"Comma separated list of keywords to help searches for the {name}",
    )(f)

    f = click.option("--default-directory", help="Set the default directory")(f)

    f = click.option(
        "--force-encryption/--no-force-encryption",
        default=None,
        help=f"Force the {name} to encrypt transfers",
    )(f)
    f = click.option(
        "--disable-verify/--no-disable-verify",
        default=None,
        is_flag=True,
        help=f"Set the {name} to ignore checksum verification",
    )(f)

    return f
