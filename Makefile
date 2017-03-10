VIRTUALENV=.venv

.PHONY: docs build upload localdev test clean help

help:
	@echo "These are our make targets and what they do."
	@echo "All unlisted targets are internal."
	@echo ""
	@echo "  help:      Show this helptext"
	@echo "  localdev:  Setup local development env with a 'setup.py develop'"
	@echo "  build:     Create the distributions which we like to upload to pypi"
	@echo "  test:      Run the full suite of tests"
	@echo "  docs:      Clean old HTML docs and rebuild them with sphinx"
	@echo "  upload:    [build], but also upload to pypi using twine"
	@echo "  clean:     Remove typically unwanted files, mostly from [build]"
	@echo "  all:       Wrapper for [localdev] + [docs] + [test]"


all: localdev docs test

$(VIRTUALENV):
	virtualenv $(VIRTUALENV)


localdev: $(VIRTUALENV)
	$(VIRTUALENV)/bin/python setup.py develop


build: $(VIRTUALENV)
	$(VIRTUALENV)/bin/python setup.py sdist bdist_egg


$(VIRTUALENV)/bin/twine: $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install twine==1.6.5

upload: $(VIRTUALENV)/bin/twine build
	$(VIRTUALENV)/bin/twine upload dist/*


$(VIRTUALENV)/bin/flake8 $(VIRTUALENV)/bin/nose2: test-requirements.txt $(VIRTUALENV)
	$(VIRTUALENV)/bin/pip install -r test-requirements.txt
	touch $(VIRTUALENV)/bin/flake8
	touch $(VIRTUALENV)/bin/nose2t

test: $(VIRTUALENV)/bin/flake8 $(VIRTUALENV)/bin/nose2 localdev
	$(VIRTUALENV)/bin/flake8
	$(VIRTUALENV)/bin/nose2 --verbose


# docs needs full localdev install because sphinx will actually try to do
# imports! Otherwise, we'll be missing dependencies like `requests`
docs: localdev
	$(VIRTUALENV)/bin/pip install sphinx==1.4.1
	-rm -r docs
	mkdir docs
	touch docs/.nojekyll
	. $(VIRTUALENV)/bin/activate && $(MAKE) -C docs-source/ html


clean:
	-rm -r $(VIRTUALENV)
	-rm -r dist
	-rm -r build
	-rm -r *.egg-info
