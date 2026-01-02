"""
This is a very small 'tox' plugin.
'toxfile.py' is a special name for auto-loading a plugin without defining package
metadata.

For full doc, see: https://tox.wiki/en/latest/plugins.html

Methods decorated below with `tox.plugin.impl` are hook implementations.
We only implement hooks which we need.
"""

from __future__ import annotations

import contextvars
import logging
import os
import typing as t

from tox.plugin import impl

if t.TYPE_CHECKING:
    from tox.execute import Outcome
    from tox.tox_env.api import ToxEnv

log = logging.getLogger(__name__)


GH_GROUP: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "GH_GROUP", default=None
)


def on_gh_actions() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def gh_group_start(name: str) -> None:
    if on_gh_actions():
        # when starting a group, close any previous group
        # needed for install -> run
        #
        # also make sure it is "reentry" safe, since on_install fires multiple times
        # (see detailed note below)
        if prior_group := GH_GROUP.get():
            if prior_group != name:
                print("::endgroup::")
                print(f"::group::tox:{name}")
                GH_GROUP.set(name)
        else:
            print(f"::group::tox:{name}")
            GH_GROUP.set(name)


def gh_group_end() -> None:
    if on_gh_actions():
        print("::endgroup::")
        GH_GROUP.set(None)


@impl
def tox_on_install(
    tox_env: ToxEnv, arguments: t.Any, section: str, of_type: str
) -> None:
    # the install block is generic in name so that the name does not change as this hook
    # fires multiple times while tox is spinning up a new environment
    # experimentally, we see
    # - env specific on_install
    # - env specific on_install (again?!)
    # - .pkg on_install
    # - env specific on_install again
    gh_group_start("install")


@impl
def tox_before_run_commands(tox_env: ToxEnv) -> None:
    # determine if it was a parallel invocation by examining the CLI command
    parallel_detected = tox_env.options.command in ("p", "run-parallel")
    if parallel_detected:
        # tox is running parallel, set an indicator env var
        # and effectively disable pytest-xdist by setting xdist-workers to 0
        # -- 0 means tests will run in the main process, not even in a worker
        setenv = tox_env.conf.load("set_env")
        setenv.update({"TOX_PARALLEL": "1", "PYTEST_XDIST_AUTO_NUM_WORKERS": "0"})

    gh_group_start(f"{tox_env.name}:run")


@impl
def tox_after_run_commands(
    tox_env: ToxEnv, exit_code: int, outcomes: list[Outcome]
) -> None:
    gh_group_end()
