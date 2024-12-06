import os


def is_remote_session() -> bool:
    return bool(os.environ.get("SSH_TTY", os.environ.get("SSH_CONNECTION")))
