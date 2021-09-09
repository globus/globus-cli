import click
from pkg_resources import load_entry_point


def walk_contexts(name="globus", cmd=None, parent_ctx=None):
    """
    A recursive walk over click Contexts for all commands in a tree
    Returns the results in a tree-like structure as triples,
      (context, subcommands, subgroups)

    subcommands is a list of contexts
    subgroups is a list of (context, subcommands, subgroups) triples
    """
    if cmd is None:
        cmd = load_entry_point("globus-cli", "console_scripts", "globus")
    current_ctx = click.Context(cmd, info_name=name, parent=parent_ctx)
    cmds, groups = [], []
    for subcmdname, subcmd in getattr(cmd, "commands", {}).items():
        # explicitly skip hidden commands
        if subcmd.hidden:
            continue

        if isinstance(subcmd, click.Group):
            groups.append(walk_contexts(subcmdname, subcmd, current_ctx))
        else:
            cmds.append(click.Context(subcmd, info_name=subcmdname, parent=current_ctx))

    return (current_ctx, cmds, groups)


def iter_all_contexts(tree=None):
    ctx, subcmds, subgroups = tree or walk_contexts()
    yield ctx
    yield from subcmds
    for g in subgroups:
        yield from iter_all_contexts(g)


def is_repeatable(o):
    return o.count or o.multiple


def compute_nargs(o):
    if o.is_flag or o.count:
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
