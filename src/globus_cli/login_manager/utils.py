import os


def is_remote_session():
    return os.environ.get("SSH_TTY", os.environ.get("SSH_CONNECTION"))
