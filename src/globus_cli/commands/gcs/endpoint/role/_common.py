from globus_cli.services.auth import CustomAuthClient
from globus_cli.termio import Field
from globus_cli.termio.formatters.auth import PrincipalURNFormatter


def role_fields(auth_client: CustomAuthClient) -> list[Field]:
    return [
        Field("ID", "id"),
        Field("Role", "role"),
        Field("Principal", "principal", formatter=PrincipalURNFormatter(auth_client)),
    ]
