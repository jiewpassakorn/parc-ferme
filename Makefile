.PHONY: install dev clean test coverage profiles help

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: $(VENV) ## Install project
	$(PIP) install -e .

dev: $(VENV) ## Install with dev dependencies
	$(PIP) install -e ".[dev]"

$(VENV):
	python3 -m venv $(VENV)

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=parc_ferme --cov-report=term-missing

profiles: ## List available profiles
	$(VENV)/bin/parc-ferme --list-profiles

clean: ## Remove venv and build artifacts
	rm -rf $(VENV) *.egg-info src/*.egg-info dist build __pycache__
