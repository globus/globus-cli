# run via `tox r -e check-mindeps-lower-bounds`
import pathlib
import re
import sys
import tomllib

import mddj.api
from packaging.dependency_groups import DependencyGroupResolver
from packaging.requirements import Requirement

dj = mddj.api.DJ()
REPO_ROOT = pathlib.Path(__file__).parent.parent

# load 'test-mindeps', filtered only to the directly declared requirements, not the
# includes
with open(REPO_ROOT / "pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)

group_resolver = DependencyGroupResolver(pyproject["dependency-groups"])
mindeps = [
    r for r in group_resolver.lookup("test-mindeps") if isinstance(r, Requirement)
]

dependencies: tuple[str, ...] = dj.read.dependencies()
dependency_lower_bounds = {}
for dep in dependencies:
    req = Requirement(dep)

    # extract lower bounds via a regex
    # this pattern is imperfect but is good enough for realistic versions
    # it won't work on complex specifiers with multiple `>=` expressions, for example
    match = re.search(r">=([0-9\.a-z]+)", str(req.specifier))
    if match is None:
        continue

    dependency_lower_bounds[req.name] = match.group(1)

for req in mindeps:
    if req.name not in dependency_lower_bounds:
        print(f"warning: {req} is in 'test-mindeps' but is not in dependencies")
        continue

    true_lower_bound = dependency_lower_bounds[req.name]
    if not req.specifier.contains(true_lower_bound):
        print(
            f"ERROR: 'test-mindeps' lists {req}, which does not contain "
            f"the true lower bound, {true_lower_bound!r}"
        )
        sys.exit(1)
