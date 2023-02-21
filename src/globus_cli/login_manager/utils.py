import os

# the contract version number for the LoginManager's scope behavior
# this will be annotated on every token acquired and stored, in order to see what
# version we were at when we got a token
# make sure it is available to the LoginManager and the tokenstorage module
CURRENT_SCOPE_CONTRACT_VERSION: int = 1


def is_remote_session():
    return os.environ.get("SSH_TTY", os.environ.get("SSH_CONNECTION"))
