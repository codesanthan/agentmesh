.PHONY: setup test lint format check examples clean

setup:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check .

format:
	ruff format .

check: lint test

examples:
	agentmesh run examples/research_team/workflow.yaml
	agentmesh run examples/customer_support/workflow.yaml

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache build dist *.egg-info src/*.egg-info
