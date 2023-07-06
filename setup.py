import os
import re

from setuptools import find_packages, setup

TEST_REQUIREMENTS = [
    "coverage<7",
    "pytest<7",
    "pytest-xdist<3",
    "pytest-timeout<2",
    "responses==0.17.0",
    # loading test fixture data
    "ruamel.yaml==0.17.16",
]
DEV_REQUIREMENTS = TEST_REQUIREMENTS + [
    "tox<4",
    "scriv==0.17.0",
]


def parse_version():
    # single source of truth for package version
    version_string = ""
    version_pattern = re.compile(r'__version__ = "([^"]*)"')
    with open(os.path.join("src", "globus_cli", "version.py")) as f:
        for line in f:
            match = version_pattern.match(line)
            if match:
                version_string = match.group(1)
                break
    if not version_string:
        raise RuntimeError("Failed to parse version information")
    return version_string


def read_readme():
    with open("README.rst") as fp:
        return fp.read()


setup(
    name="globus-cli",
    version=parse_version(),
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    install_requires=[
        "globus-sdk==3.23.0",
        "click>=8.0.0,<9",
        "jmespath==1.0.1",
        "packaging>=17.0",
        # these are dependencies of the SDK, but they are used directly in the CLI
        # declare them here in case the underlying lib ever changes
        "requests>=2.19.1,<3.0.0",
        "cryptography>=3.3.1",
        # depend on the latest version of typing-extensions on python versions which do
        # not have all of the typing features we use
        'typing_extensions>=4.0;python_version<"3.11"',
    ],
    extras_require={"test": TEST_REQUIREMENTS, "development": DEV_REQUIREMENTS},
    entry_points={"console_scripts": ["globus = globus_cli:main"]},
    # descriptive info, non-critical
    description="Globus CLI",
    long_description=read_readme(),
    author="Stephen Rosen",
    author_email="sirosen@globus.org",
    url="https://github.com/globus/globus-cli",
    keywords=["globus", "cli", "command line"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
