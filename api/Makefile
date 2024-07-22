tests:
	pytest -s --cov-config=setup.cfg
	flake8
	mypy .

separator_linter = ============================= Linter =============================
separator_type = ============================= Type checker =============================

tests-log:
	pytest > tests_result.log
	echo $(separator_linter) >> tests_result.log
	flake8 >> tests_result.log
	echo $(separator_type) >> tests_result.log
	mypy . >> tests_result.log

clean:
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	python3 -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*_cache')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('htmlcov')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('.coverage')]"

.PHONY: tests
