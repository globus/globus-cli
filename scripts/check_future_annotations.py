#!/usr/bin/env python3
"""
A linter which scans python files to see if they import Optional or Union without also
importing future annotations. All modules using these names should do the future import
so that pyupgrade has a chance to rewrite usages.
"""
from __future__ import annotations

import argparse
import ast
import glob
import os
import sys

ROOTDIR = os.path.dirname(os.path.dirname(__file__))


def all_py_filenames(files):
    if not files:
        yield from glob.glob(os.path.join(ROOTDIR, "**/*.py"), recursive=True)
    else:
        yield from files


FLAGGABLE_NAMES = frozenset(
    {
        "Optional",
        "Union",
    }
)


class ScanningVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.found_flagged_usage = False
        self.has_future_import = False
        self.known_name_of_imported_typing: str | None = None

    @property
    def forbidden_strings(self):
        if self.known_name_of_imported_typing is None:
            return FLAGGABLE_NAMES
        return [f"{self.known_name_of_imported_typing}.{x}" for x in FLAGGABLE_NAMES]

    def _check_annotations(self, annotation_node):
        unparsed = ast.unparse(annotation_node)
        if any((x + "[") in unparsed for x in self.forbidden_strings):
            self.found_flagged_usage = True

    def generic_visit(self, node):
        if self.found_flagged_usage:
            return
        else:
            super().generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "typing":
                self.known_name_of_imported_typing = (
                    alias.asname if alias.asname else alias.name
                )

    def visit_ImportFrom(self, node):
        if node.module == "__future__" and "annotations" in (
            alias.name for alias in node.names
        ):
            self.has_future_import = True
        elif node.module == "typing" and any(
            name in (alias.name for alias in node.names) for name in FLAGGABLE_NAMES
        ):
            self.found_flagged_usage = True

    def visit_FunctionDef(self, node):
        if node.returns is not None:
            self._check_annotations(node.returns)
        self.generic_visit(node)


def check_file(filename):
    visitor = ScanningVisitor()
    with open(filename) as fp:
        tree = ast.parse(fp.read(), filename=filename)
    visitor.visit(tree)
    if visitor.found_flagged_usage and visitor.has_future_import is False:
        print(f"{filename} failed the future annotations check!")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("files", nargs="*", help="default: all python files")
    args = parser.parse_args()

    success = True
    for filename in all_py_filenames(args.files):
        success = check_file(filename) and success

    if not success:
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
