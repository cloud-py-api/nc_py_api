.DEFAULT_GOAL := help

.PHONY: docs
.PHONY: html
docs html:
	rm -rf docs/_build
	$(MAKE) -C docs html

.PHONY: links
links:
	$(MAKE) -C docs links

.PHONY: help
help:
	@echo "Welcome to NC_PY_API development. Please use \`make <target>\` where <target> is one of"
	@echo "  docs                make HTML docs"
	@echo "  html                make HTML docs"
	@echo "  "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  register27          register nc_py_api for Nextcloud 27"
	@echo "  register28          register nc_py_api for Nextcloud 28"
	@echo "  register            register nc_py_api for Nextcloud Last"
	@echo "  "
	@echo "  tests27             run nc_py_api tests for Nextcloud 27"
	@echo "  tests28             run nc_py_api tests for Nextcloud 28"
	@echo "  tests               run nc_py_api tests for Nextcloud Last"

.PHONY: register27
register27:
	/bin/sh scripts/dev_register.sh master-stable27-1 stable27.local

.PHONY: register28
register28:
	/bin/sh scripts/dev_register.sh master-stable28-1 stable28.local

.PHONY: register
register:
	/bin/sh scripts/dev_register.sh master-nextcloud-1 nextcloud.local

.PHONY: tests27
tests27:
	NEXTCLOUD_URL=http://stable27.local python3 -m pytest

.PHONY: tests28
tests28:
	NEXTCLOUD_URL=http://stable28.local python3 -m pytest

.PHONY: tests
tests:
	NEXTCLOUD_URL=http://nextcloud.local python3 -m pytest
