tests:
	pytest -s
	flake8
	mypy .

.PHONY: tests
