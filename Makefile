tests:
	pytest -s --cov=. --cov-report=html
	flake8
	mypy .

.PHONY: tests
