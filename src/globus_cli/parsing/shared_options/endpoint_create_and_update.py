from __future__ import annotations

import sys
import typing as t

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal
if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never

import click

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def _apply_universal_endpointish_params(
    f: C, name: str, *, display_name: Literal["argument", "option", "null"] = "null"
) -> C:
    if display_name == "argument":
        f = click.argument("DISPLAY_NAME")(f)
    elif display_name == "option":
        f = click.option("--display-name", help=f"Name for the {name}")(f)
    elif display_name == "null":
        pass
    else:
        assert_never()

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


def endpointish_create_and_update_params(
    mode: Literal["create", "update"], name: str = "endpoint"
) -> t.Callable[[C], C]:
    if mode == "create":

        def decorator(f: C) -> C:
            return _apply_universal_endpointish_params(f, name, display_name="argument")

    elif mode == "update":

        def decorator(f: C) -> C:
            return _apply_universal_endpointish_params(f, name, display_name="option")

    else:
        assert_never()

    return decorator
