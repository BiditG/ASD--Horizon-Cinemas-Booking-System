.PHONY: lint test security ci build

lint:
	flake8 src/ --max-line-length=120 --exclude=__pycache__ --count --statistics
	pylint src/ --fail-under=7.0

test:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

security:
	bandit -r src/ -ll
	safety check -r requirements.txt

ci: lint test security

build:
	python build_submission.py
