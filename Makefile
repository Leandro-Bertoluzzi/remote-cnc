start-app:
	cd src && python main.py

run-tests:
	cd src && pytest -s
	cd src && flake8
	cd src && mypy .

# unit-tests: TBD
# feature-tests: TBD
# desktop-e2e-tests: TBD

clean:
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	python3 -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*_cache')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.log')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('htmlcov')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('.coverage')]"

.PHONY: clean
