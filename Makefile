# ---------------------------------------------------------------------------
# Remote CNC – Makefile
# ---------------------------------------------------------------------------
# Requires: uv (https://docs.astral.sh/uv/)
# ---------------------------------------------------------------------------

SRC     := src
UV_RUN  := cd $(SRC) && uv run
COMPOSE := docker compose

# ===== Setup ==============================================================

.PHONY: install sync lock

install:          ## First-time setup: install uv, sync deps, create venv
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	cd $(SRC) && uv sync

sync:             ## Install / update all workspace deps from lockfile
	cd $(SRC) && uv sync

lock:             ## Re-resolve & update uv.lock
	cd $(SRC) && uv lock

# ===== Quality ============================================================

.PHONY: test test-core test-api test-worker test-desktop lint typecheck check

test:             ## Run all tests
	$(UV_RUN) pytest

test-core:        ## Run core / shared tests only
	$(UV_RUN) pytest tests/

test-api:         ## Run API tests only
	$(UV_RUN) pytest api/tests/

test-worker:      ## Run worker tests only
	$(UV_RUN) pytest worker/tests/

test-desktop:     ## Run desktop tests only
	$(UV_RUN) pytest desktop/tests/

lint:             ## Run flake8 linter
	$(UV_RUN) flake8

typecheck:        ## Run mypy type checker
	$(UV_RUN) mypy .

check: lint typecheck test   ## lint + typecheck + test

# ===== Run ================================================================

.PHONY: start-desktop start-api start-worker

start-desktop:    ## Launch the desktop (PyQt5) app
	$(UV_RUN) python desktop/main.py

start-api:        ## Launch the API with uvicorn (dev)
	$(UV_RUN) uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

start-worker:     ## Launch the Celery worker locally
	$(UV_RUN) celery --app worker.main worker --loglevel=INFO

# ===== Database ===========================================================

.PHONY: db-upgrade db-downgrade db-revision db-seed

db-upgrade:       ## Apply pending Alembic migrations
	cd $(SRC)/core && uv run alembic upgrade head

db-downgrade:     ## Revert last Alembic migration
	cd $(SRC)/core && uv run alembic downgrade -1

db-revision:      ## Auto-generate a new Alembic revision (pass MSG="description")
	cd $(SRC)/core && uv run alembic revision --autogenerate -m "$(MSG)"

db-seed:          ## Seed the database with initial data
	$(UV_RUN) python db_seeder.py

# ===== Docker =============================================================

.PHONY: docker-up docker-up-sim docker-down docker-build docker-logs

docker-up:        ## Start API + infra (no worker)
	$(COMPOSE) up -d

docker-up-sim:    ## Start everything including simulated worker
	$(COMPOSE) --profile simulator up -d

docker-down:      ## Stop all containers
	$(COMPOSE) down

docker-build:     ## Rebuild Docker images
	$(COMPOSE) build

docker-logs:      ## Tail logs of all containers
	$(COMPOSE) logs -f

# ===== Cleanup ============================================================

.PHONY: clean

clean:            ## Remove compiled files, caches, logs, coverage
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
	python3 -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*_cache')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.log')]"
	python3 -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('htmlcov')]"
	python3 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('.coverage')]"
