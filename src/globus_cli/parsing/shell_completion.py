import os

import click

from globus_cli.termio import print_experimental_completion

# pulled by running `_GLOBUS_COMPLETE=source globus` in a bash shell
BASH_SHELL_COMPLETER = r"""
_globus_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _GLOBUS_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

_globus_completion_setup() {
    complete -o nosort -F _globus_completion globus
}

_globus_completion_setup;
"""  # noqa: E501

# pulled by running `_GLOBUS_COMPLETE=source_zsh globus` in a zsh shell
ZSH_SHELL_COMPLETER = r"""
#compdef globus

_globus_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[globus] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _GLOBUS_COMPLETE=zsh_complete globus)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _globus_completion globus;
"""  # noqa: E501


def print_completer_option(f):
    def callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return

        if value == "BASH":
            detected = "bash"
        elif value == "ZSH":
            detected = "zsh"
        else:  # auto
            detected = "bash"  # default to bash completion
            if "SHELL" in os.environ:  # see if shell matches, e.g. `/bin/zsh`
                if os.environ["SHELL"].endswith("zsh"):
                    detected = "zsh"

        if detected == "bash":
            click.echo(BASH_SHELL_COMPLETER)
        elif detected == "zsh":
            click.echo(ZSH_SHELL_COMPLETER)
        else:
            raise NotImplementedError("Unsupported shell completion")

        click.get_current_context().exit(0)

    def _compopt(flag, value):
        return click.option(
            flag,
            hidden=True,
            is_eager=True,
            expose_value=False,
            flag_value=value,
            callback=callback,
        )

    f = _compopt("--completer", "auto")(f)
    f = _compopt("--bash-completer", "BASH")(f)
    f = _compopt("--zsh-completer", "ZSH")(f)

    def experimental_callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        shell = value if value != "auto" else None
        print_experimental_completion(shell)
        click.get_current_context().exit(0)

    def experimental_compopt(flag, value):
        return click.option(
            flag,
            hidden=True,
            is_eager=True,
            expose_value=False,
            flag_value=value,
            callback=experimental_callback,
        )

    f = experimental_compopt("--experimental-completer", "auto")(f)
    f = experimental_compopt("--experimental-zsh-completer", "zsh")(f)
    f = experimental_compopt("--experimental-bash-completer", "bash")(f)
    return f
