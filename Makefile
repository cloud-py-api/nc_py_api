.DEFAULT_GOAL := help

.PHONY: doc
.PHONY: html
doc html:
	$(MAKE) -C docs html

.PHONY: help
help:
	@echo "Welcome to NC_PY_API development. Please use \`make <target>\` where <target> is one of"
	@echo "  doc                make HTML docs"
	@echo "  html               make HTML docs"
