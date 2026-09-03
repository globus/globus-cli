from __future__ import annotations

import os
import typing as t

import click

C = t.TypeVar("C", bound=t.Union[t.Callable[..., t.Any], click.Command])

# Output collected by running `_GLOBUS_COMPLETE=bash_source globus`
BASH_SHELL_COMPLETER = r"""
_globus_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _GLOBUS_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
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

# Output collected by running `_GLOBUS_COMPLETE=fish_source globus`
FISH_SHELL_COMPLETER = r"""
function _globus_completion;
    set -l response (env _GLOBUS_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) globus);

    for completion in $response;
        set -l metadata (string split "," $completion);

        if test $metadata[1] = "dir";
            __fish_complete_directories $metadata[2];
        else if test $metadata[1] = "file";
            __fish_complete_path $metadata[2];
        else if test $metadata[1] = "plain";
            echo $metadata[2];
        end;
    end;
end;

complete --no-files --command globus --arguments "(_globus_completion)";
"""  # noqa: E501

# Output collected by running `_GLOBUS_COMPLETE=zsh_source globus`
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

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    # autoload from fpath, call function directly
    _globus_completion "$@"
else
    # eval/source/. command, register function for later
    compdef _globus_completion globus
fi
"""  # noqa: E501


def print_completer_option(f: C) -> C:
    def callback(ctx: click.Context, param: click.Parameter, value: str | None) -> None:
        # if `resilient_parsing=True`, shell completion is being executed, so we should
        # be careful to skip the callback contents, which would echo output and exit
        if not value or ctx.resilient_parsing:
            return

        if value == "BASH":
            detected = "bash"
        elif value == "FISH":
            detected = "fish"
        elif value == "ZSH":
            detected = "zsh"
        else:  # auto
            detected = "bash"  # default to bash completion
            if "SHELL" in os.environ:  # see if shell matches, e.g. `/bin/zsh`
                if os.environ["SHELL"].endswith("zsh"):
                    detected = "zsh"
            elif "FISH_VERSION" in os.environ:
                detected = "fish"

        if detected == "bash":
            click.echo(BASH_SHELL_COMPLETER)
        elif detected == "fish":
            click.echo(FISH_SHELL_COMPLETER)
        elif detected == "zsh":
            click.echo(ZSH_SHELL_COMPLETER)
        else:
            raise NotImplementedError("Unsupported shell completion")

        click.get_current_context().exit(0)

    def _compopt(flag: str, value: str) -> t.Callable[[C], C]:
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
    f = _compopt("--fish-completer", "FISH")(f)
    f = _compopt("--zsh-completer", "ZSH")(f)
    return f
