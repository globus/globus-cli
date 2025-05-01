"""
This is a very small 'tox' plugin.
'toxfile.py' is a special name for auto-loading a plugin without defining package
metadata.

For full doc, see: https://tox.wiki/en/latest/plugins.html

Methods decorated below with `tox.plugin.impl` are hook implementations.
We only implement hooks which we need.
"""

from __future__ import annotations

import logging
import pathlib
import shutil
import typing as t

from tox.plugin import impl

if t.TYPE_CHECKING:
    from tox.config.sets import EnvConfigSet
    from tox.session.state import State
    from tox.tox_env.api import ToxEnv

log = logging.getLogger(__name__)

_INJECT_SITECUSTOMIZE = '''
"""A sitecustomize.py injected by globus_cli_coverage_sitecustomize"""
import coverage

coverage.process_startup()
'''


@impl
def tox_add_env_config(env_conf: EnvConfigSet, state: State) -> None:
    env_conf.add_config(
        keys=["globus_cli_rmtree"],
        of_type=list[str],
        default=[],
        desc="A dir tree to remove before running the environment commands",
    )
    env_conf.add_config(
        keys=["globus_cli_coverage_sitecustomize"],
        of_type=bool,
        default=[],
        desc="Inject a sitecustomize.py to enable `coverage` under pytest-xdist",
    )


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

    cli_rmtree = tox_env.conf.load("globus_cli_rmtree")
    for name in cli_rmtree:
        path = pathlib.Path(name)
        if path.exists():
            log.warning(f"globus_cli_rmtree: {path}")
            shutil.rmtree(path)

    if tox_env.conf.load("globus_cli_coverage_sitecustomize"):
        site_packages_path = pathlib.Path(tox_env.conf.load("env_site_packages_dir"))
        inject_sitecustomize_path = site_packages_path / "sitecustomize.py"
        inject_sitecustomize_path.write_text(_INJECT_SITECUSTOMIZE)

        # It is important that the tox configuration also sets
        # COVERAGE_PROCESS_START to the coverage configuration file.
        # If this is not done, `coverage.process_startup` will be a no-op.
        setenv = tox_env.conf.load("set_env")
        setenv.update({"COVERAGE_PROCESS_START": "pyproject.toml"})
