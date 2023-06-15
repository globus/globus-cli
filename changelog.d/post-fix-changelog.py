#!/usr/bin/env python
"""
This is a small "fixer" script which is meant to modify scriv-generated changelog
content to match the style of adoc content which we need for our changelog
"""

import argparse
import re

MD_H1_PATTERN = re.compile(r"^(#) (.+)$", re.MULTILINE)
MD_H2_PATTERN = re.compile(r"^(##) (.+)$", re.MULTILINE)
MD_H3_PATTERN = re.compile(r"^(###) (.+)$", re.MULTILINE)
SCRIV_LINK_PATTERN = re.compile(
    r"\n<a id='changelog\-\d+\.\d+\.\d+'></a>\n", re.MULTILINE
)


def process_file(filename):
    with open(filename) as f:
        content = f.read()

    content = MD_H1_PATTERN.sub(r"== \2", content)
    content = MD_H2_PATTERN.sub(r"\2:", content)
    content = SCRIV_LINK_PATTERN.sub("\n", content)

    with open(filename, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("FILES", nargs="*")
    args = parser.parse_args()

    if not args.FILES:
        process_file("changelog.adoc")

    for filename in args.FILES:
        process_file(filename)


if __name__ == "__main__":
    main()
