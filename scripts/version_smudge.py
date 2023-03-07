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
    smudge_value: str,
) -> None:
    print(f"smudging version in {PRETTYPATH} (smudge={smudge_value}) ... ", end="")
    with open(VERSION_PATH) as fp:
        content = fp.read()
    match = re.search('^__version__ = "([^"]+)"$', content, flags=re.MULTILINE)
    if not match:
        raise Abort(f"{PRETTYPATH} did not contain version pattern")

    old_version = match.group(1)
    old_str = f'__version__ = "{old_version}"'
    new_str = f'__version__ = "{old_version}.{smudge_value}"'
    content = content.replace(old_str, new_str)
    with open(VERSION_PATH, "w") as fp:
        fp.write(content)
    print("ok")


def revert_smudge() -> None:
    print(f"reverting smudged version in {PRETTYPATH} ... ", end="")
    with open(VERSION_PATH) as fp:
        content = fp.read()
    match = re.search('^__version__ = "([^"]+)"$', content, flags=re.MULTILINE)
    if not match:
        raise Abort(f"{PRETTYPATH} did not contain version pattern")

    old_version = match.group(1)
    unsmudged = ".".join(old_version.split(".")[:3])
    old_str = f'__version__ = "{old_version}"'
    new_str = f'__version__ = "{unsmudged}"'
    content = content.replace(old_str, new_str)
    with open(VERSION_PATH, "w") as fp:
        fp.write(content)
    print("ok")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smudge-value",
        help="set a smudge value -- defaults to 'devX' where 'X' is the epoch",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="remove any smudge value from the version",
    )
    args = parser.parse_args()

    if not args.smudge_value:
        args.smudge_value = f"dev{int(time.time())}"

    if args.revert:
        revert_smudge()
    else:
        bump_version_in_file(args.smudge_value)


if __name__ == "__main__":
    main()
