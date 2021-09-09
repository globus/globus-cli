import click

from ._common import compute_nargs, iter_all_contexts, opt_strs, slamopts


class BashCompleter:
    PROLOGUE = """\
declare -A __globus_comp_subcmds
declare -A __globus_comp_opts
declare -A __globus_comp_opt_nargs
declare -A __globus_comp_slamopts
declare -A __globus_comp_opt_choices
"""

    EPILOGUE = """
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

complete -F _globus_comp_bash globus"""  # noqa: E501

    def _print_common_info(self, ctx):
        options = [
            x
            for x in ctx.command.params
            if isinstance(x, click.Option) and not x.hidden
        ]
        joined_opts = " ".join(x for o in options for x in opt_strs(o))
        joined_slamopts = " ".join(x for o in options for x in slamopts(o))
        click.echo(f'__globus_comp_opts["{ctx.command_path}"]="{joined_opts}"')
        click.echo(f'__globus_comp_slamopts["{ctx.command_path}"]="{joined_slamopts}"')
        for o in options:
            nargs = compute_nargs(o)
            for s in opt_strs(o):
                click.echo(
                    f'__globus_comp_opt_nargs["{ctx.command_path} {s}"]="{nargs}"'
                )
        for o in options:
            if isinstance(o.type, click.Choice):
                choices = " ".join(o.type.choices)
                for s in opt_strs(o):
                    click.echo(
                        "__globus_comp_opt_choices"
                        f'["{ctx.command_path} {s}"]="{choices}"'
                    )

    def _print_cmd_info(self, ctx):
        # commands do not have any subcommands
        click.echo(f'__globus_comp_subcmds["{ctx.command_path}"]=""')
        self._print_common_info(ctx)

    def _print_group_info(self, ctx):
        command_names = ctx.command.commands.keys()
        cmds = " ".join(command_names)
        click.echo(f'__globus_comp_subcmds["{ctx.command_path}"]="{cmds}"')
        self._print_common_info(ctx)

    def print_completion(self):
        click.echo(self.PROLOGUE)
        for ctx in iter_all_contexts():
            if isinstance(ctx.command, click.Group):
                self._print_group_info(ctx)
            else:
                self._print_cmd_info(ctx)
        click.echo(self.EPILOGUE)
