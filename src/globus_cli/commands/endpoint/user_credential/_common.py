import functools
import typing as t

import click


def user_credential_id_arg(
    f: t.Optional[t.Callable] = None, *, metavar: str = "USER_CREDENTIAL_ID"
):
    if f is None:
        return functools.partial(user_credential_id_arg, metavar=metavar)
    return click.argument("user_credential_id", metavar=metavar, type=click.UUID)(f)


def user_credential_create_and_update_params(
    f: t.Optional[t.Callable] = None, *, create: bool = False
) -> t.Callable:
    """
    Collection of options consumed by user credential create and update.
    Passing create as True makes any values required for create
    arguments instead of options.
    """
    if f is None:
        return functools.partial(
            user_credential_create_and_update_params, create=create
        )

    # identity_id, username, and storage gateway are required for create
    # and immutable on update
    if create:
        f = click.argument("local-username")(f)
        f = click.argument("globus-identity")(f)
        f = click.argument("storage-gateway")(f)

    f = click.option("--display-name", help="Display name for the credential.")(f)

    return f
