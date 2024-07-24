test-api:
	cd api && pytest -s
	cd api && flake8
	cd api && mypy .

test-core:
	cd core && pytest -s
	cd core && flake8
	cd core && mypy .

test-desktop:
	cd desktop && pytest -s
	cd desktop && flake8
	cd desktop && mypy .

clean:
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	python3 -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*_cache')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.log')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('htmlcov')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('.coverage')]"

.PHONY: clean
