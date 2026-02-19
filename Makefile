.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Welcome to NC_PY_API development. Please use \`make <target>\` where <target> is one of"
	@echo "  "
	@echo "  Next commands are only for dev environment with nextcloud-docker-dev!"
	@echo "  They should run from the host you are developing on(with activated venv) and not in the container with Nextcloud!"
	@echo "  "
	@echo "  register31          register nc_py_api for Nextcloud 31"
	@echo "  register32          register nc_py_api for Nextcloud 32"
	@echo "  register33          register nc_py_api for Nextcloud 33"
	@echo "  register            register nc_py_api for Nextcloud Last"
	@echo "  "
	@echo "  tests31             run nc_py_api tests for Nextcloud 31"
	@echo "  tests32             run nc_py_api tests for Nextcloud 32"
	@echo "  tests33             run nc_py_api tests for Nextcloud 33"
	@echo "  tests               run nc_py_api tests for Nextcloud Last"

.PHONY: register31
register31:
	/bin/sh scripts/dev_register.sh master-stable31-1 stable31.local

.PHONY: register32
register32:
	/bin/sh scripts/dev_register.sh master-stable32-1 stable32.local

.PHONY: register33
register33:
	/bin/sh scripts/dev_register.sh master-stable33-1 stable33.local

.PHONY: register
register:
	/bin/sh scripts/dev_register.sh master-nextcloud-1 nextcloud.local

.PHONY: tests31
tests31:
	NEXTCLOUD_URL=http://stable31.local python3 -m pytest

.PHONY: tests32
tests32:
	NEXTCLOUD_URL=http://stable32.local python3 -m pytest

.PHONY: tests33
tests33:
	NEXTCLOUD_URL=http://stable33.local python3 -m pytest

.PHONY: tests
tests:
	NEXTCLOUD_URL=http://nextcloud.local python3 -m pytest
