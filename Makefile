tests:
	pytest -s --cov-config=setup.cfg
	flake8
	mypy .

.PHONY: tests
