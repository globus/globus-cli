import typing as t

import click
import globus_sdk

from globus_cli.types import AnyCommand
from globus_cli.parsing import OMITTABLE_STRING

C = t.TypeVar("C", bound=AnyCommand)


def user_credential_id_arg(
    *, metavar: str = "USER_CREDENTIAL_ID"
) -> t.Callable[[C], C]:
    return click.argument("user_credential_id", metavar=metavar, type=click.UUID)


def user_credential_create_and_update_params(
    *, create: bool = False
) -> t.Callable[[C], C]:
    """
    Collection of options consumed by user credential create and update.
    Passing create as True makes any values required for create
    arguments instead of options.
    """

    def decorator(f: C) -> C:
        # identity_id, username, and storage gateway are required for create
        # and immutable on update
        if create:
            f = click.argument("local-username")(f)
            f = click.argument("globus-identity")(f)
            f = click.argument("storage-gateway", type=click.UUID)(f)

        f = click.option(
            "--display-name",
            help="Display name for the credential.",
            default=globus_sdk.MISSING,
            type=OMITTABLE_STRING,
        )(f)

        return f

    return decorator
