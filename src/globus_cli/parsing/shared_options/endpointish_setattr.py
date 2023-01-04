from __future__ import annotations

import sys
import typing as t

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

import click

from globus_cli.endpointish import EntityType
from globus_cli.parsing.param_types import CommaDelimitedList, StringOrNull

C = t.TypeVar("C", bound=t.Union[t.Callable, click.Command])


def endpointish_setattr_params(
    operation: Literal["create", "update"],
    *,
    entity_types: tuple[EntityType, ...],
    name: Literal["endpoint", "collection"] = "endpoint",
    overrides: dict[str, str] | None = None,
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
    display_name_style = "argument" if operation == "create" else "option"
    if all((e in EntityType.traditional_endpoints()) for e in entity_types):
        keyword_style = "string"
        verify_style = "flag"
    elif all((e not in EntityType.traditional_endpoints()) for e in entity_types):
        keyword_style = "list"
        verify_style = "choice"
    else:
        raise NotImplementedError(
            "entity types in a mix of styles, cannot build options"
        )

    # apply overrides
    overrides = overrides or {}
    display_name_style = overrides.get("display_name_style", display_name_style)
    keyword_style = overrides.get("keyword_style", keyword_style)
    verify_style = overrides.get("verify_style", verify_style)

    def decorator(f: C) -> C:
        return _apply_universal_endpointish_params(
            f,
            name,
            display_name_style=display_name_style,
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
    if display_name_style == "argument":
        f = click.argument("DISPLAY_NAME")(f)
    elif display_name_style == "option":
        f = click.option("--display-name", help=f"Name for the {name}")(f)
    else:
        raise NotImplementedError()

    f = click.option(
        "--description", help=f"Description for the {name}", type=StringOrNull()
    )(f)
    f = click.option(
        "--info-link", help=f"Link for info about the {name}", type=StringOrNull()
    )(f)
    f = click.option(
        "--contact-info", help=f"Contact info for the {name}", type=StringOrNull()
    )(f)
    f = click.option(
        "--contact-email", help=f"Contact email for the {name}", type=StringOrNull()
    )(f)
    f = click.option(
        "--organization", help=f"Organization for the {name}", type=StringOrNull()
    )(f)
    f = click.option(
        "--department",
        help=f"Department which operates the {name}",
        type=StringOrNull(),
    )(f)
    f = click.option(
        "--keywords",
        type=str if keyword_style == "string" else CommaDelimitedList(),
        help=f"Comma separated list of keywords to help searches for the {name}",
    )(f)

    f = click.option(
        "--default-directory",
        type=StringOrNull(),
        help=f"Default directory when browsing or executing tasks on the {name}",
    )(f)

    f = click.option(
        "--force-encryption/--no-force-encryption",
        default=None,
        help=f"Force the {name} to encrypt transfers",
    )(f)
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
        f = click.option(
            "--verify",
            type=click.Choice(["force", "disable", "default"], case_sensitive=False),
            callback=_verify_choice_to_dict,
            help=verify_help,
        )(f)
    else:
        f = click.option(
            "--disable-verify/--no-disable-verify",
            default=None,
            is_flag=True,
            help=f"Set the {name} to ignore checksum verification",
        )(f)
    return f


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
