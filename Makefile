.DEFAULT_GOAL := help

.PHONY: docs
.PHONY: html
docs html:
	$(MAKE) -C docs html

.PHONY: help
help:
	@echo "Welcome to NC_PY_API development. Please use \`make <target>\` where <target> is one of"
	@echo "  docs                make HTML docs"
	@echo "  html                make HTML docs"
	@echo "  "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  register            register nc_py_api in host as an application(requires activated venv)"
	@echo "                      this should run from the host you are developing on, not in a container with Nextcloud"
	@echo "                      and only last Nextcloud version(28) is supported, for other versions tests runs on GitHub"
	@echo "  tests               run nc_py_api tests to check that registration was successful"

.PHONY: register
register:
	/bin/sh scripts/dev_register.sh

.PHONY: tests
tests:
	python3 -m pytest
