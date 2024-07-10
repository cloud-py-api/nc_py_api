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
	@echo "  register28          register nc_py_api for Nextcloud 28"
	@echo "  register29          register nc_py_api for Nextcloud 29"
	@echo "  register30          register nc_py_api for Nextcloud 30"
	@echo "  register            register nc_py_api for Nextcloud Last"
	@echo "  "
	@echo "  tests28             run nc_py_api tests for Nextcloud 28"
	@echo "  tests29             run nc_py_api tests for Nextcloud 29"
	@echo "  tests30             run nc_py_api tests for Nextcloud 30"
	@echo "  tests               run nc_py_api tests for Nextcloud Last"

.PHONY: register28
register28:
	/bin/sh scripts/dev_register.sh master-stable28-1 stable28.local

.PHONY: register29
register29:
	/bin/sh scripts/dev_register.sh master-stable29-1 stable29.local

.PHONY: register30
register30:
	/bin/sh scripts/dev_register.sh master-stable30-1 stable30.local

.PHONY: register
register:
	/bin/sh scripts/dev_register.sh master-nextcloud-1 nextcloud.local

.PHONY: tests28
tests28:
	NEXTCLOUD_URL=http://stable28.local python3 -m pytest

.PHONY: tests29
tests29:
	NEXTCLOUD_URL=http://stable29.local python3 -m pytest

.PHONY: tests30
tests30:
	NEXTCLOUD_URL=http://stable30.local python3 -m pytest

.PHONY: tests
tests:
	NEXTCLOUD_URL=http://nextcloud.local python3 -m pytest
