#!/usr/bin/env python3
"""completion generator for globus-cli"""
import contextlib
import sys
import textwrap

import click
from pkg_resources import load_entry_point

CLI = load_entry_point("globus-cli", "console_scripts", "globus")


def walk_contexts(name="globus", cmd=CLI, parent_ctx=None):
    """
    A recursive walk over click Contexts for all commands in a tree
    Returns the results in a tree-like structure as triples,
      (context, subcommands, subgroups)

    subcommands is a list of contexts
    subgroups is a list of (context, subcommands, subgroups) triples
    """
    current_ctx = click.Context(cmd, info_name=name, parent=parent_ctx)
    cmds, groups = [], []
    for subcmdname, subcmd in getattr(cmd, "commands", {}).items():
        # explicitly skip hidden commands
        if subcmd.hidden:
            continue

        cmds.append(click.Context(subcmd, info_name=subcmdname, parent=current_ctx))

        if isinstance(subcmd, click.Group):
            groups.append(walk_contexts(subcmdname, subcmd, current_ctx))

    return (current_ctx, cmds, groups)


def iter_all_contexts(tree=None):
    ctx, subcmds, subgroups = tree or walk_contexts()
    yield ctx
    yield from subcmds
    for g in subgroups:
        yield from iter_all_contexts(g)


def compute_nargs(o):
    if o.is_flag:
        return 0
    else:
        return o.nargs


def opt_strs(o):
    return list(o.opts) + list(o.secondary_opts)


def slamopts(o):
    # two letter options, like `-F` can be slammed if they consume exactly one argument
    if compute_nargs(o) != 1:
        return []
    return [x for x in (list(o.opts) + list(o.secondary_opts)) if len(x) < 3]


class Completer:
    def print_completion(self):
        raise NotImplementedError


class BashCompleter(Completer):
    PROLOGUE = textwrap.dedent(
        """
        declare -A __globus_comp_subcmds
        declare -A __globus_comp_opts
        declare -A __globus_comp_opt_nargs
        declare -A __globus_comp_slamopts
        declare -A __globus_comp_opt_choices
        """
    )

    EPILOGUE = textwrap.dedent(
        """\
        __globus_comp_parse_line() {
          local compword
          compword="${COMP_WORDS[$COMP_CWORD]}"

          local boundary
          boundary=$((${#COMP_WORDS[@]} - 2))

          local i=0 toskip=0
          local curopt="" nomoreopts=0
          local curcmd=${COMP_WORDS[0]} curword=${COMP_WORDS[0]}
          while [ $i -lt $boundary ]; do
            _=$((i++))
            curword=${COMP_WORDS[$i]}

            if [ "$curword" = "--" ]; then
              curopt=""
              nomoreopts=1
              continue
            fi

            if [ $toskip -gt 0 ]; then
              _=$((toskip--))
              continue
            fi

            if [[ $nomoreopts -eq 0 ]] && [[ $curword == -* ]]; then
              # if a "slammed" option like `-Ftext` is given, proceed to the next word
              # in the command
              slamopts=${__globus_comp_slamopts[$curcmd]}
              for opt in $slamopts; do
                if [[ "$curword" != "$opt" ]] && [[ "$curword" == "$opt"* ]]; then
                  continue 2
                fi
              done

              curopt=$curword
              toskip=${__globus_comp_opt_nargs["$curcmd $curword"]}
              [ -n "$toskip" ] || toskip=0
              continue
            fi

            for subcmd in ${__globus_comp_subcmds["$curcmd"]}; do
              if [ "$curword" = "$subcmd" ]; then
                curcmd="$curcmd $curword"
                continue 2
              fi
            done

            # if this point is reached, the command structure is unrecognized
            # (e.g. 'globus enpdoint foo'); end with the current discovered command
            # (i.e. 'globus endpoint')
            break
          done
          if [ $toskip -eq 0 ]; then
            curopt=""
          fi

          # if no partial option processing is happening, check to see if the current
          # word, when added, matches a command
          if [ "$toskip" -eq 0 ]; then
            for subcmd in ${__globus_comp_subcmds["$curcmd"]}; do
              if [ "$compword" = "$subcmd" ]; then
                curcmd="$curcmd $compword"
                curopt=""
                break
              fi
            done
          fi
          echo "$curcmd"
          echo "$curopt"
          echo "$toskip"
        }

        __globus_comp_add_match_to_compreply() {
          for choice in $1; do
            if [[ "$choice" == "${COMP_WORDS[$COMP_CWORD]}"* ]]; then
              COMPREPLY+=("$choice")
            fi
          done
        }

        __globus_comp_add_match_for_cmdopt() {
          local choices="${__globus_comp_opt_choices["$1"]}"
          if [ -n "$choices" ]; then
            __globus_comp_add_match_to_compreply "$choices"
          fi
        }

        _globus_comp_bash() {
          COMPREPLY=()
          local curword
          curword="${COMP_WORDS[$COMP_CWORD]}"

          local parsed
          readarray -t parsed < <(__globus_comp_parse_line)

          local curcmd curopt num_optargs curcmd_w_curopt
          curcmd=${parsed[0]}
          curopt=${parsed[1]}
          num_optargs=${parsed[2]}
          curcmd_w_curopt="$curcmd $curopt"

          case $curword in
            -*)  # option case
              __globus_comp_add_match_to_compreply "${__globus_comp_opts["$curcmd"]}"
              ;;
            "")  # next subcommand, option, or option value if no partial word
              if [ "$num_optargs" -gt 0 ]; then
                __globus_comp_add_match_for_cmdopt "$curcmd_w_curopt"
              else
                for subcmd in ${__globus_comp_subcmds["$curcmd"]}; do
                  COMPREPLY+=("$subcmd")
                done
              fi
              ;;
            *)  # partial word case, subcommand or option argument
              if [ -z "$curopt" ]; then
                __globus_comp_add_match_to_compreply "${__globus_comp_subcmds["$curcmd"]}"
              else
                __globus_comp_add_match_for_cmdopt "$curcmd_w_curopt"
              fi
              ;;
          esac
        }

        complete -F _globus_comp_bash globus
        """  # noqa: E501
    )

    def _print_common_info(self, ctx):
        options = [
            x
            for x in ctx.command.params
            if isinstance(x, click.Option) and not x.hidden
        ]
        joined_opts = " ".join(x for o in options for x in opt_strs(o))
        joined_slamopts = " ".join(x for o in options for x in slamopts(o))
        print(f'__globus_comp_opts["{ctx.command_path}"]="{joined_opts}"')
        print(f'__globus_comp_slamopts["{ctx.command_path}"]="{joined_slamopts}"')
        for o in options:
            nargs = compute_nargs(o)
            for s in opt_strs(o):
                print(f'__globus_comp_opt_nargs["{ctx.command_path} {s}"]="{nargs}"')
        for o in options:
            if isinstance(o.type, click.Choice):
                choices = " ".join(o.type.choices)
                for s in opt_strs(o):
                    print(
                        "__globus_comp_opt_choices"
                        f'["{ctx.command_path} {s}"]="{choices}"'
                    )

    def _print_cmd_info(self, ctx):
        # commands do not have any subcommands
        print(f'__globus_comp_subcmds["{ctx.command_path}"]=""')
        self._print_common_info(ctx)

    def _print_group_info(self, ctx):
        command_names = ctx.command.commands.keys()
        cmds = " ".join(command_names)
        print(f'__globus_comp_subcmds["{ctx.command_path}"]="{cmds}"')
        self._print_common_info(ctx)

    def print_completion(self):
        print(self.PROLOGUE)
        self.print_data()
        for ctx in iter_all_contexts():
            if isinstance(ctx.command, click.Group):
                self._print_group_info(ctx)
            else:
                self._print_cmd_info(ctx)
        print(self.EPILOGUE)


class ZshCompleter(Completer):
    EPILOGUE = "compdef _globus_comp_cmd_globus globus"

    def _is_root_ctx(self, ctx):
        return ctx.command_path == "globus"

    def _cmdslug(self, ctx):
        return ctx.command_path.replace(" ", "_").replace("-", "_")

    def _cmd_completer_name(self, ctx):
        return f"_globus_comp_cmd_{self._cmdslug(ctx)}"

    def _subcmd_describer_name(self, ctx):
        return f"_globus_comp_describe_subcmds_{self._cmdslug(ctx)}"

    @contextlib.contextmanager
    def _in_completion_func(self, ctx):
        print(f"{self._cmd_completer_name(ctx)}() {{")
        if self._is_root_ctx(ctx):
            print("  local line\n")
        yield
        print("}")

    @contextlib.contextmanager
    def _in_subcmd_describer(self, ctx):
        print(f"{self._subcmd_describer_name(ctx)}() {{")
        print("  local subcmds")
        print("  subcmds=(")
        yield
        print("  )")
        print(f"  _describe -t subcmds '{ctx.command_path} command' subcmds \"$@\"")
        print("}")

    @contextlib.contextmanager
    def _in_line_case(self, ctx):
        print("  case $line[1] in")
        yield
        print("  esac")

    def _option_descs(self, o):
        nargs = compute_nargs(o)
        spec = ""
        if isinstance(o.type, click.Choice):
            spec = ": :(" + " ".join(o.type.choices) + ")"
        elif nargs > 0:
            spec = ": :( )"

        helptext = f"[{o.help}]".replace('"', '\\"')
        # TODO: determine if we need '=[...]' in our spec
        # if nargs > 0:
        #     helptext = f"={helptext}"

        flags = opt_strs(o)
        for flag in flags:
            yield f'"({flag}){flag}{helptext}{spec}"'

    def _all_option_descs(self, ctx):
        options = [
            x
            for x in ctx.command.params
            if isinstance(x, click.Option) and not x.hidden
        ]
        return [x for o in options for x in self._option_descs(o)]

    def _print_cmd_completer(self, ctx):
        with self._in_completion_func(ctx):
            print("  _arguments \\")
            print("    " + " \\\n    ".join(self._all_option_descs(ctx)))

    def _print_group_completer(self, ctx):
        subcommand_names = ctx.command.commands.keys()
        with self._in_subcmd_describer(ctx):
            for n in subcommand_names:
                cmdhelp = ctx.command.commands[n].get_short_help_str()
                print(f'    "{n}:{cmdhelp}"')

        with self._in_completion_func(ctx):
            print("  _arguments -C \\")
            for desc in self._all_option_descs(ctx):
                print(f"    {desc} \\")
            print(f'    "1: :{self._subcmd_describer_name(ctx)}" \\')
            print('    "*::arg:->args"\n')

            with self._in_line_case(ctx):
                for n in subcommand_names:
                    funcname = f"{self._cmd_completer_name(ctx)}_{n.replace('-', '_')}"
                    print(f'    "{n}")')
                    print(f"      {funcname}")
                    print("      ;;")

    def print_completion(self):
        for ctx in iter_all_contexts():
            if isinstance(ctx.command, click.Group):
                self._print_group_completer(ctx)
            else:
                self._print_cmd_completer(ctx)
        print(self.EPILOGUE)


def print_data(shell):
    if shell.lower() == "zsh":
        ZshCompleter().print_completion()
    else:
        BashCompleter().print_completion()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_data(sys.argv[1])
    else:
        print_data("bash")
