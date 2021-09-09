import os

from .bash_impl import BashCompleter
from .zsh_impl import ZshCompleter


def get_completer_cls(shell=None):
    if shell is None:
        shell = "bash"  # default to bash completion
        if "SHELL" in os.environ:  # see if shell matches, e.g. `/bin/zsh`
            if os.environ["SHELL"].endswith("zsh"):
                shell = "zsh"
    return {
        "zsh": ZshCompleter,
        "bash": BashCompleter,
    }.get(shell, BashCompleter)


def print_completion(shell=None):
    completer_cls = get_completer_cls(shell=shell)
    completer_cls().print_completion()
