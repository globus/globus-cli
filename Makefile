PYTHON_VERSION=python3
CLI_VERSION=$(shell grep '^__version__' src/globus_cli/version.py | cut -d '"' -f2)

.venv:
	virtualenv --python=$(PYTHON_VERSION) .venv
	.venv/bin/pip install -U pip setuptools
	.venv/bin/pip install -e '.[development]'

.PHONY: localdev
localdev: .venv


.PHONY: lint test reference
lint:
	tox -e lint,mypy
reference:
	tox -e reference
test:
	tox

.PHONY: showvars prepare-release tag-release
showvars:
	@echo "CLI_VERSION=$(CLI_VERSION)"
prepare-release:
	tox -e prepare-release
	$(EDITOR) changelog.adoc
tag-release:
	git tag -s "$(CLI_VERSION)" -m "v$(CLI_VERSION)"
	-git push $(shell git rev-parse --abbrev-ref @{push} | cut -d '/' -f1) refs/tags/$(CLI_VERSION)

.PHONY: update-dependencies
update-dependencies:
	python ./scripts/update_dependencies.py

.PHONY: clean
clean:
	rm -rf .venv .tox dist build *.egg-info
