import typing as t

from globus_cli import utils

from .scopes import CLI_SCOPE_REQUIREMENTS


class MissingLoginError(ValueError):
    def __init__(
        self, missing_servers: t.Sequence[str], *, assume_gcs=False, assume_flow=False
    ):
        self.missing_servers = missing_servers
        self.assume_gcs = assume_gcs
        self.assume_flow = assume_flow

        self.server_names = sorted(_resolve_server_names(missing_servers))

        server_string = utils.format_list_of_words(*self.server_names)
        message_prefix = utils.format_plural_str(
            "Missing {login}",
            {"login": "logins"},
            len(missing_servers) != 1,
        )

        login_cmd = "globus login"
        if assume_gcs:
            login_cmd = "globus login " + " ".join(
                [f"--gcs {s}" for s in missing_servers]
            )
        elif assume_flow:
            login_cmd = "globus login " + " ".join(
                f"--flow {server}" for server in missing_servers
            )

        self.message = (
            message_prefix + f" for {server_string}, please run:\n\n  {login_cmd}\n"
        )
        super().__init__(self.message)

    def __str__(self):
        return self.message


def _resolve_server_names(server_names: t.Sequence[str]) -> t.Iterator[str]:
    for name in server_names:
        try:
            req = CLI_SCOPE_REQUIREMENTS.get_by_resource_server(name)
            yield req["nice_server_name"]
        except LookupError:
            yield name
