#!/usr/bin/env python
from __future__ import annotations

import argparse
import pathlib
import re
import time

REPO_ROOT = pathlib.Path(__file__).parent.parent
VERSION_PATH = REPO_ROOT / "src" / "globus_cli" / "version.py"
PRETTYPATH = VERSION_PATH.relative_to(REPO_ROOT)


class Abort(RuntimeError):
    pass


def bump_version_in_file(
    dev_version: int,
) -> None:
    dev_slug = f"dev{dev_version}"
    print(f"setting dev version in {PRETTYPATH} ({dev_slug}) ... ", end="")
    with open(VERSION_PATH) as fp:
        content = fp.read()
    match = re.search('^__version__ = "([^"]+)"$', content, flags=re.MULTILINE)
    if not match:
        raise Abort(f"{PRETTYPATH} did not contain version pattern")

    old_version = match.group(1)
    old_str = f'__version__ = "{old_version}"'
    new_str = f'__version__ = "{old_version}.{dev_slug}"'
    content = content.replace(old_str, new_str)
    with open(VERSION_PATH, "w") as fp:
        fp.write(content)
    print("ok")


def revert_version() -> None:
    print(f"reverting dev version in {PRETTYPATH} ... ", end="")
    with open(VERSION_PATH) as fp:
        content = fp.read()
    match = re.search('^__version__ = "([^"]+)"$', content, flags=re.MULTILINE)
    if not match:
        raise Abort(f"{PRETTYPATH} did not contain version pattern")

    old_version = match.group(1)
    restored = ".".join(old_version.split(".")[:3])
    old_str = f'__version__ = "{old_version}"'
    new_str = f'__version__ = "{restored}"'
    content = content.replace(old_str, new_str)
    with open(VERSION_PATH, "w") as fp:
        fp.write(content)
    print("ok")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--number",
        type=int,
        help="set the development release number -- defaults to 'int(time.time())'",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="remove any 'dev' version specifier from the version",
    )
    args = parser.parse_args()

    if not args.number:
        args.number = int(time.time())

    if args.revert:
        revert_version()
    else:
        bump_version_in_file(args.number)


if __name__ == "__main__":
    main()
