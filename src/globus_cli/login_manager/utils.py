import os
import typing as t

from globus_cli.login_manager.client_login import is_client_login
from globus_cli.login_manager.tokenstore import read_well_known_config


def is_remote_session() -> bool:
    return bool(os.environ.get("SSH_TTY", os.environ.get("SSH_CONNECTION")))


def get_current_identity_id() -> str:
    """
    Return the current user's identity ID.
    For a client-authorized invocation, that's the client ID.
    """

    if is_client_login():
        return os.environ["GLOBUS_CLI_CLIENT_ID"]
    else:
        user_data = read_well_known_config("auth_user_data", allow_null=False)
        return t.cast(str, user_data["sub"])
