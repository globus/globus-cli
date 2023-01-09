from __future__ import annotations

import sys
import typing as t

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

if sys.version_info < (3, 9):
    DictType = t.Dict
else:
    DictType = dict

import click

from globus_cli import utils
from globus_cli.parsing.param_classes import AnnotatedOption
from globus_cli.parsing.param_types import CommaDelimitedList, StringOrNull

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def endpointish_setattr_params(
    operation: Literal["create", "update"],
    *,
    name: Literal["endpoint", "collection"] = "endpoint",
    # default for display_name_style is that it is deduced from 'operation'
    display_name_style: Literal["argument", "option"] | None = None,
    keyword_style: Literal["string", "list"] = "list",
    verify_style: Literal["flag", "choice"] = "choice",
) -> t.Callable[[C], C]:
    """
    This helper provides arguments and options for "endpointish" entity types.
    It spans "create" and "update" commands, and is named "setattr" because it helps set
    attributes on the new or updated entity.

    It translates "high level" options which describe the operation being performed into
    "low level" options which describe the behavior which is appropriate.

    :param operation: Is the command a "create" or an "update"?
    :param name: What is the entity name, "collection" or "endpoint"?
    """
    default_display_name_style = "argument" if operation == "create" else "option"

    def decorator(f: C) -> C:
        return _apply_universal_endpointish_params(
            f,
            name,
            display_name_style=display_name_style or default_display_name_style,
            keyword_style=keyword_style,
            verify_style=verify_style,
        )

    return decorator


def _apply_universal_endpointish_params(
    f: C,
    name: Literal["endpoint", "collection"],
    *,
    display_name_style: str,
    keyword_style: str,
    verify_style: str,
) -> C:
    decorators: list[t.Callable[[C], C]] = []

    if display_name_style == "argument":
        decorators.append(click.argument("DISPLAY_NAME"))
    elif display_name_style == "option":
        decorators.append(click.option("--display-name", help=f"Name for the {name}"))
    else:
        raise NotImplementedError()

    decorators.extend(
        [
            click.option(
                "--description", help=f"Description for the {name}", type=StringOrNull()
            ),
            click.option(
                "--info-link",
                help=f"Link for info about the {name}",
                type=StringOrNull(),
            ),
            click.option(
                "--contact-info",
                help=f"Contact info for the {name}",
                type=StringOrNull(),
            ),
            click.option(
                "--contact-email",
                help=f"Contact email for the {name}",
                type=StringOrNull(),
            ),
            click.option(
                "--organization",
                help=f"Organization for the {name}",
                type=StringOrNull(),
            ),
            click.option(
                "--department",
                help=f"Department which operates the {name}",
                type=StringOrNull(),
            ),
            click.option(
                "--keywords",
                type=str if keyword_style == "string" else CommaDelimitedList(),
                help="Comma separated list of keywords to help searches "
                f"for the {name}",
            ),
            click.option(
                "--default-directory",
                type=StringOrNull(),
                help="Default directory when browsing or executing tasks "
                f"on the {name}",
            ),
            click.option(
                "--force-encryption/--no-force-encryption",
                default=None,
                help=f"Force the {name} to encrypt transfers",
            ),
        ]
    )

    if verify_style == "choice":
        verify_help = (
            f"Set the policy for this {name} for file integrity verification "
            "after transfer. 'force' requires all transfers to perform "
            "verfication. 'disable' disables all verification checks. 'default' "
            "allows the user to decide on verification at Transfer task submit  "
            "time."
        )
        if name == "collection":
            verify_help += (
                " When set on mapped collections, this policy is inherited by any "
                "guest collections"
            )
        decorators.append(
            click.option(
                "--verify",
                type=click.Choice(
                    ["force", "disable", "default"], case_sensitive=False
                ),
                callback=_verify_choice_to_dict,
                help=verify_help,
                type_annotation=DictType[str, bool],
                cls=AnnotatedOption,
            )
        )
    else:
        decorators.append(
            click.option(
                "--disable-verify/--no-disable-verify",
                default=None,
                is_flag=True,
                help=f"Set the {name} to ignore checksum verification",
            )
        )

    return utils.fold_decorators(f, decorators)


def _verify_choice_to_dict(
    ctx: click.Context, param: click.Parameter, value: t.Any
) -> dict[str, bool]:
    if value is None:
        return {}
    value = value.lower()
    if value == "force":
        return {"force_verify": True, "disable_verify": False}
    elif value == "disable":
        return {"force_verify": False, "disable_verify": True}
    else:
        return {"force_verify": False, "disable_verify": False}
