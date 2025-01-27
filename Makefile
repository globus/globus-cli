CLI_VERSION=$(shell grep '^__version__' src/globus_cli/version.py | cut -d '"' -f2)

.venv:
	python -m venv --upgrade-deps .venv
	.venv/bin/pip install -e '.'
	# TODO: update once `pip` v25.1 is released to use `pip install --group`
	.venv/bin/pip install dependency-groups
	.venv/bin/pip-install-dependency-groups dev

.PHONY: install
install: .venv


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
tag-release:
	git tag -s "$(CLI_VERSION)" -m "v$(CLI_VERSION)"
	-git push $(shell git rev-parse --abbrev-ref @{push} | cut -d '/' -f1) refs/tags/$(CLI_VERSION)

.PHONY: update-dependencies
update-dependencies:
	python ./scripts/update_dependencies.py

.PHONY: clean
clean:
	rm -rf .venv .tox dist build *.egg-info
