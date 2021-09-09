import contextlib
import re

import click

from ._common import compute_nargs, is_repeatable, iter_all_contexts, opt_strs

_ZSH_HELP_ESC_RE = re.compile(r'([`":\[\]])')


class ZshCompleter:
    EPILOGUE = "compdef _globus_comp_cmd_globus globus"

    def __init__(self):
        self._indent = 0

    def _p(self, s):
        click.echo(" " * self._indent + s)

    def _is_root_ctx(self, ctx):
        return ctx.command_path == "globus"

    def _cmdslug(self, ctx):
        return ctx.command_path.replace(" ", "_").replace("-", "_")

    def _cmd_completer_name(self, ctx):
        return f"_globus_comp_cmd_{self._cmdslug(ctx)}"

    def _subcmd_describer_name(self, ctx):
        return f"_globus_comp_describe_subcmds_{self._cmdslug(ctx)}"

    @contextlib.contextmanager
    def indent(self, n=2):
        self._indent += n
        yield
        self._indent -= n

    @contextlib.contextmanager
    def _in_completion_func(self, ctx):
        self._p(f"{self._cmd_completer_name(ctx)}() {{")
        with self.indent():
            if self._is_root_ctx(ctx):
                self._p('local curcontext="$curcontext" context state state_descr line')
                self._p("typeset -A opt_args")
            yield
        self._p("}")

    @contextlib.contextmanager
    def _in_subcmd_describer(self, ctx):
        self._p(f"{self._subcmd_describer_name(ctx)}() {{")
        with self.indent():
            self._p("local -a subcmds; subcmds=(")
            with self.indent():
                yield
            self._p(")")
            self._p(f"_describe -t subcmds '{ctx.command_path} command' subcmds \"$@\"")
        self._p("}")

    @contextlib.contextmanager
    def _in_line_case(self, ctx):
        self._p("case $state in (args) case $line[1] in")
        with self.indent():
            yield
        self._p("esac ;; esac")

    def _option_descs(self, o):
        nargs = compute_nargs(o)
        argspec = ""
        if isinstance(o.type, click.Choice):
            argspec = ": :(" + " ".join(o.type.choices) + ")"
        elif nargs > 0:
            argspec = ": :( )"

        # escape quotes and colons
        helptext = "[" + _ZSH_HELP_ESC_RE.sub(r"\\\1", o.help) + "]"

        # TODO: add mutual exclusivity info from mutexinfo
        # when options are listed in the parenthetical section at the start of an option
        # spec, they are noted as mutually exclusive
        # here we list aliases, so that `--help` and `-h` are considered mutex (for
        # better completion)
        raw_flags = flags = opt_strs(o)

        # append a + if a flag takes one argument and is a short option
        # this indicates that we support option-slamming, as in `-Fjson`
        flags = [
            (f"{flag}+" if len(flag) == 2 and nargs == 1 else flag) for flag in flags
        ]
        # append an = if a flag takes one argument and is a long option
        # this indicates that we support `--format=text`
        flags = [
            (f"{flag}=" if flag.startswith("--") and nargs == 1 else flag)
            for flag in flags
        ]
        if is_repeatable(o):
            flags = [f"*{flag}" for flag in flags]

        if len(flags) == 1:
            yield f'"{flags[0]}{helptext}{argspec}"'
        else:
            for flag in flags:
                yield ('"(' + " ".join(raw_flags) + ")" + f'{flag}{helptext}{argspec}"')

    def _all_option_descs(self, ctx):
        options = [
            x
            for x in ctx.command.params
            if isinstance(x, click.Option) and not x.hidden
        ]
        return [x for o in options for x in self._option_descs(o)]

    def _print_cmd_completer(self, ctx):
        with self._in_completion_func(ctx):
            self._p("_arguments \\")
            with self.indent():
                all_descs = list(self._all_option_descs(ctx))
                for d in all_descs[:-1]:
                    self._p(f"{d}  \\")
                self._p(all_descs[-1])

    def _print_group_completer(self, ctx):
        subcommand_names = ctx.command.commands.keys()
        with self._in_subcmd_describer(ctx):
            for n in subcommand_names:
                cmdhelp = ctx.command.commands[n].get_short_help_str()
                self._p(f'"{n}:{cmdhelp}"')

        with self._in_completion_func(ctx):
            self._p("_arguments -C \\")
            with self.indent():
                for desc in self._all_option_descs(ctx):
                    self._p(f"{desc} \\")
                # IMPORTANT!
                # This is subtle, but each of these specs MUST have '(-)', indicating
                # mutual exclusivity with additional CLI options
                # This prevents the higher-level command in a tree from eagerly
                # consuming options which follow subcommands
                #
                # For example, if the input command is `globus endpoint -h`, we *don't*
                # want the `_arguments` call to consume `-h` as an option to the
                # `globus` command
                # It should instead be left un-parsed, and the subsequent `_arguments`
                # call for the `endpoint` subcommand will pick it up correctly
                #
                # This behavior has been tested and does not mark these matches as
                # mutually exclusive with prior options. Meaning that
                # `globus -Fjson <TAB>` will run the subcommand description action as
                # desired
                self._p(f'"(-): :{self._subcmd_describer_name(ctx)}" \\')
                self._p('"(-)*::arg:->args"')

            with self._in_line_case(ctx):
                for n in subcommand_names:
                    funcname = f"{self._cmd_completer_name(ctx)}_{n.replace('-', '_')}"
                    self._p(f'"{n}") {funcname} ;;')

    def print_completion(self):
        for ctx in iter_all_contexts():
            if isinstance(ctx.command, click.Group):
                self._print_group_completer(ctx)
            else:
                self._print_cmd_completer(ctx)
        self._p(self.EPILOGUE)
