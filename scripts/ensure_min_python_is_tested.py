# run via `tox r -e check-min-python-is-tested`
import pathlib
import sys

import mddj.api
import ruamel.yaml

dj = mddj.api.DJ()
YAML = ruamel.yaml.YAML(typ="safe")
REPO_ROOT = pathlib.Path(__file__).parent.parent

requires_python_version = dj.read.requires_python(lower_bound=True)
print("requires-python:", requires_python_version)

with open(REPO_ROOT / ".github/workflows/test.yaml") as f:
    workflow = YAML.load(f)
includes = workflow["jobs"]["test"]["strategy"]["matrix"]["include"]
for include in includes:
    if include["name"] == "Linux":
        break
else:
    raise ValueError("Could not find 'Linux' in the test matrix.")

for environment in include["tox-post-environments"]:
    if environment.endswith("-mindeps"):
        break
else:
    raise ValueError("Could not find a '-mindeps' tox-post-environment.")

python_version, _, _ = environment.partition("-")
if python_version != f"py{requires_python_version}":
    print("ERROR: ensure_min_python_is_tested.py failed!")
    print(
        f"\nPackage data sets 'Requires-Python: >={requires_python_version}', "
        f"but the test-mindeps job is configured to test '{python_version}'.\n",
        file=sys.stderr,
    )
    sys.exit(1)


tox_min_python_version = dj.read.tox.min_python_version()
if tox_min_python_version != requires_python_version:
    print("ERROR: ensure_min_python_is_tested.py failed!")
    print(
        f"\nPackage data sets 'Requires-Python: >={requires_python_version}', "
        "but tox is configured to test with a minimum of "
        f"'{tox_min_python_version}'.\n",
        file=sys.stderr,
    )
    sys.exit(1)
