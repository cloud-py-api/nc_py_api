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
	@echo "  register28          register nc_py_api for Nextcloud 28"
	@echo "  register27          register nc_py_api for Nextcloud 27"
	@echo "  register26          register nc_py_api for Nextcloud 26"
	@echo "  "
	@echo "  tests28             run nc_py_api tests for Nextcloud 28"
	@echo "  tests27             run nc_py_api tests for Nextcloud 27"
	@echo "  tests26             run nc_py_api tests for Nextcloud 26"

.PHONY: register28
register28:
	/bin/sh scripts/dev_register.sh master-nextcloud-1 nextcloud.local

.PHONY: register27
register27:
	/bin/sh scripts/dev_register.sh master-stable27-1 stable27.local

.PHONY: register26
register26:
	/bin/sh scripts/dev_register.sh master-stable26-1 stable26.local

.PHONY: tests28
tests28:
	NEXTCLOUD_URL=http://nextcloud.local python3 -m pytest

.PHONY: tests27
tests27:
	NEXTCLOUD_URL=http://stable27.local python3 -m pytest

.PHONY: tests26
tests26:
	NEXTCLOUD_URL=http://stable26.local python3 -m pytest
