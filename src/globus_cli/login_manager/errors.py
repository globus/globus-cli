import typing as t

from globus_cli import utils

from .context import LoginContext
from .scopes import CLI_SCOPE_REQUIREMENTS


class MissingLoginError(ValueError):
    def __init__(
        self,
        missing_servers: t.Sequence[str],
        context: LoginContext,
    ) -> None:
        self.missing_servers = missing_servers

        error_message = context.error_message or self._default_error_message()

        self.message = f"{error_message}\nPlease run:\n\n  {context.login_command}\n"
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def _default_error_message(self) -> str:
        """
        Default error message if the context doesn't provide one.

        :returns: error message in the format:
          "Missing logins for Globus Auth and 12b3a34c-b818-4e5c-87e9-a294f43a845c."
        """

        server_names = sorted(_resolve_server_names(self.missing_servers))
        formatted_server_names = utils.format_list_of_words(*server_names)

        login = "login" if len(self.missing_servers) == 1 else "logins"
        return f"Missing {login} for {formatted_server_names}."


def _resolve_server_names(server_names: t.Sequence[str]) -> t.Iterator[str]:
    for name in server_names:
        try:
            req = CLI_SCOPE_REQUIREMENTS.get_by_resource_server(name)
            yield req["nice_server_name"]
        except LookupError:
            yield name
