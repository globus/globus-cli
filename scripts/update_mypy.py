#!/usr/bin/env python
from __future__ import annotations

import json
import pathlib
import re
import urllib.request

REPO_ROOT = pathlib.Path(__file__).parent.parent


class Abort(RuntimeError):
    pass


def get_mypy_latest() -> str:
    with urllib.request.urlopen("https://pypi.python.org/pypi/mypy/json") as conn:
        version_data = json.load(conn)
    return str(version_data["info"]["version"])


def bump_mypy_version_on_file(path: pathlib.Path, new_version: str) -> None:
    print(f"updating mypy in {path.relative_to(REPO_ROOT)} ... ", end="")
    with open(path) as fp:
        content = fp.read()
    match = re.search(r"mypy==(\d+\.\d+)", content)
    if not match:
        raise Abort(f"{path} did not contain mypy version pattern")

    old_version = match.group(1)
    old_str = f"mypy=={old_version}"
    new_str = f"mypy=={new_version}"
    content = content.replace(old_str, new_str)
    with open(path, "w") as fp:
        fp.write(content)
    print("ok")


def bump_mypy_version_in_precommit(path: pathlib.Path, new_version: str) -> None:
    print(f"updating mypy in {path.relative_to(REPO_ROOT)} ... ", end="")
    with open(path) as fp:
        content = fp.readlines()
    found_line = -1
    for lineno, line in enumerate(content):
        if line.strip() == "- repo: https://github.com/pre-commit/mirrors-mypy":
            found_line = lineno
            break
    if found_line == -1:
        raise Abort(f"{path} did not contain mypy repo line")

    target_line = found_line + 1
    if target_line >= len(content):
        raise Abort(f"{path} had mypy repo line as last line (needs rev line next)")

    match = re.search(r"\s+rev:\sv(\d+\.\d+)", content[target_line])
    if not match:
        raise Abort(f"{path} did not have rev line after repo line")

    old_version = match.group(1)
    content[target_line] = content[target_line].replace(old_version, new_version)
    with open(path, "w") as fp:
        fp.write("".join(content))
    print("ok")


def bump_mypy_version() -> None:
    new_version = get_mypy_latest()
    bump_mypy_version_on_file(REPO_ROOT / "tox.ini", new_version)
    bump_mypy_version_in_precommit(REPO_ROOT / ".pre-commit-config.yaml", new_version)


def main() -> None:
    bump_mypy_version()


if __name__ == "__main__":
    main()
