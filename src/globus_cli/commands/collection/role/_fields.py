import typing as t

import globus_sdk

from globus_cli.termio import Field
from globus_cli.termio.formatters.auth import PrincipalURNFormatter


class CollectionRoleFormatter(PrincipalURNFormatter):
    """
    A formatter for collection roles
    """

    def __init__(
        self, auth_client: globus_sdk.AuthClient, collection_role: dict[str, t.Any]
    ) -> None:
        super().__init__(auth_client)
        self.add_items(collection_role.get("id"))
        self.add_items(collection_role.get("role", ()))
        self.add_items(collection_role.get("principal"))


def collection_role_format_fields(
    auth_client: globus_sdk.AuthClient,
    collection_role: dict[str, t.Any],
) -> list[Field]:
    """
    The standard list of fields to render for a collection role.

    :param auth_client: An AuthClient, used to resolve principal URNs.
    :param collection_role: The collection role assignment to format
    """
    principal = CollectionRoleFormatter(auth_client, collection_role)

    return [
        Field("ID", "id"),
        Field("Role", "role"),
        Field("Principal", "principal", formatter=principal),
    ]
