.PHONY: install install-dev test lint format clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/ai_pr_agent --cov-report=html

lint:
	flake8 src/ai_pr_agent
	mypy src/ai_pr_agent

format:
	black src/ai_pr_agent tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Add to existing Makefile

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-fast:
	pytest -m "not slow" -v

test-all:
	pytest tests/ -v

test-coverage:
	pytest tests/ -v --cov=src/ai_pr_agent --cov-report=html --cov-report=term

test-watch:
	pytest-watch tests/ -v

# For Windows, use:
test-coverage-windows:
	pytest tests/ -v --cov=src\ai_pr_agent --cov-report=html --cov-report=term