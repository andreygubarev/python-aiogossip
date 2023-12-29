MAKEFILE_DIR := $(realpath $(dir $(firstword $(MAKEFILE_LIST))))

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: format
format: ## Format Python Package
	python -m isort .
	python -m black .

.PHONY: lint
lint: ## Lint Python Package
	python -m flake8

.PHONY: compile
compile: ## Compile Python Package and Protobuf
	protoc -I=$(MAKEFILE_DIR)/src/protos/ \
		--python_out=$(MAKEFILE_DIR)/src/aiogossip/ \
		$(MAKEFILE_DIR)/src/protos/*.proto

.PHONY: test
test: ## Test Python Package
ifeq ($(MODULE),)
	python -m pytest --pdb
else
	python -m pytest --pdb $(MAKEFILE_DIR)/tests/test_$(MODULE)*.py
endif

MODULES := $(shell (cd src/aiogossip && ls -R **/*.py) | grep -v '__init__.py')
MODULES_TESTS := $(foreach mod,$(MODULES),test_$(subst /,_,$(mod)))

.PHONY: coverage-$(MODULES_TESTS)
coverage-$(MODULES_TESTS): ## Test Python Package with Coverage
	python -m pytest --cov=$(shell grep '# MODULE: ' $(MAKEFILE_DIR)/tests/$(subst coverage-,,$@) | sed 's,# MODULE: ,,g') --cov-report=term-missing --cov-fail-under=100 --pdb $(MAKEFILE_DIR)/tests/$(subst coverage-,,$@)

.PHONY: coverage
coverage: coverage-$(MODULES_TESTS) ## Test Python Package with Coverage

.PHONY: run
run: ## Run Python Package
	python $(MAKEFILE_DIR)/examples/gossip.py

.PHONY: build
build: ## Build Python Package
	python -m build --sdist --wheel

.PHONY: install
install: ## Install Python Package
	python -m pip install -e .

.PHONY: clean
clean: ## Clean Python Package
	git clean -fdX
