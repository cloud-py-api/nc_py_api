.DEFAULT_GOAL := help

.PHONY: docs
.PHONY: html
docs html:
	rm -rf docs/_build
	$(MAKE) -C docs html

.PHONY: help
help:
	@echo "Welcome to NC_PY_API development. Please use \`make <target>\` where <target> is one of"
	@echo "  docs                make HTML docs"
	@echo "  html                make HTML docs"
	@echo "  "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  register            register nc_py_api for Nextcloud Last"
	@echo "  register27          register nc_py_api for Nextcloud 27"
	@echo "  "
	@echo "  tests               run nc_py_api tests for Nextcloud Last"
	@echo "  tests27             run nc_py_api tests for Nextcloud 27"

.PHONY: register
register:
	/bin/sh scripts/dev_register.sh master-nextcloud-1 nextcloud.local

.PHONY: register27
register27:
	/bin/sh scripts/dev_register.sh master-stable27-1 stable27.local

.PHONY: tests
tests:
	NEXTCLOUD_URL=http://nextcloud.local python3 -m pytest

.PHONY: tests27
tests27:
	NEXTCLOUD_URL=http://stable27.local python3 -m pytest
