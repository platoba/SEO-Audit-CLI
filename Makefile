.PHONY: install test lint format clean docker docker-test audit batch help

PYTHON ?= python3
PIP ?= pip3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install -e ".[reports,dev]"

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest tests/ -v --tb=short --cov=audit --cov-report=term-missing

lint: ## Run linter
	$(PYTHON) -m ruff check audit/ tests/ seo_audit.py

format: ## Auto-format code
	$(PYTHON) -m ruff format audit/ tests/ seo_audit.py

clean: ## Clean build artifacts
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

docker: ## Build Docker image
	docker build -t seo-audit-cli .

docker-test: ## Run tests in Docker
	docker compose run --rm test

audit: ## Run audit on a URL (usage: make audit URL=example.com)
	$(PYTHON) seo_audit.py $(URL)

batch: ## Run batch audit (usage: make batch FILE=urls.txt)
	$(PYTHON) seo_audit.py --batch $(FILE) --json
