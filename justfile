# ---------------------------------------------------------------------------
# Remote CNC – justfile
# ---------------------------------------------------------------------------
# Requires: just (https://just.systems), uv (https://docs.astral.sh/uv/)
# ---------------------------------------------------------------------------

# Use PowerShell 7 on Windows, sh everywhere else
set windows-shell := ["pwsh.exe", "-NoLogo", "-NoProfileLoadTime", "-Command"]

# Load .env file automatically (makes $DB_USER, $DB_NAME, etc. available)
set dotenv-load

# Show available recipes grouped by category
[private]
default:
    @just --list

# ===========================================================================
# Setup
# ===========================================================================

# Install / update all workspace deps from lockfile
[group('setup')]
[working-directory: 'src']
sync:
    uv sync

# Re-resolve & update uv.lock
[group('setup')]
[working-directory: 'src']
lock:
    uv lock

# ===========================================================================
# Quality
# ===========================================================================

# Run all tests
[group('quality')]
[working-directory: 'src']
test:
    uv run pytest

# Run core / shared tests only
[group('quality')]
[working-directory: 'src']
test-core:
    uv run pytest tests/

# Run API tests only
[group('quality')]
[working-directory: 'src']
test-api:
    uv run pytest api/tests/

# Run worker tests only
[group('quality')]
[working-directory: 'src']
test-worker:
    uv sync --package cnc-worker
    uv run pytest worker/tests/

# Run desktop tests only
[group('quality')]
[working-directory: 'src']
test-desktop:
    uv sync --package cnc-desktop
    uv run pytest desktop/tests/

# Run linter
[group('quality')]
[working-directory: 'src']
lint:
    uv run ruff check .

# Run linter with auto-fix
[group('quality')]
[working-directory: 'src']
lint-fix:
    uv run ruff check --fix .

# Run formatter
[group('quality')]
[working-directory: 'src']
format:
    uv run ruff format .

# Run type checker
[group('quality')]
[working-directory: 'src']
typecheck:
    uv run ty check

# Run lint + typecheck + tests
[group('quality')]
check: lint typecheck test

# ===========================================================================
# Run
# ===========================================================================

# Launch the API with uvicorn (dev, with reload)
[group('run')]
[working-directory: 'src']
start-api:
    uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Launch the desktop (PyQt5) app
[group('run')]
[working-directory: 'src']
start-desktop:
    uv run python -m desktop.main

# Launch the desktop app with auto-reload on file changes
[group('run')]
[working-directory: 'src']
start-desktop-watch:
    uv run watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- python -m desktop.main

# Launch the Celery worker
[group('run')]
[working-directory: 'src']
start-worker:
    uv run celery --app worker.main worker --loglevel=INFO

# Launch the Celery worker with auto-reload on file changes
[group('run')]
[working-directory: 'src']
start-worker-watch:
    uv run watchmedo auto-restart --directory=./ --pattern=*.py -- celery --app worker.main worker --loglevel=INFO --logfile=logs/celery.log

# ===========================================================================
# Database
# ===========================================================================

# Apply pending Alembic migrations (local)
[group('database')]
[working-directory: 'src/core']
db-upgrade:
    uv run alembic upgrade head

# Revert last Alembic migration (local)
[group('database')]
[working-directory: 'src/core']
db-downgrade:
    uv run alembic downgrade -1

# Auto-generate a new Alembic revision — usage: just db-revision "description"
[group('database')]
[working-directory: 'src/core']
db-revision msg:
    uv run alembic revision --autogenerate -m "{{msg}}"

# Seed the database with initial data (local)
[group('database')]
[working-directory: 'src']
db-seed:
    uv run python db_seeder.py

# Export the full DB schema as a SQL script (outputs to src/core/db_schema.sql)
[group('database')]
[working-directory: 'src/core']
db-generate-schema:
    uv run alembic upgrade head --sql > db_schema.sql

# Export SQL for a range of migrations — usage: just db-generate-migration <start_rev> <end_rev>
[group('database')]
[working-directory: 'src/core']
db-generate-migration start end:
    uv run alembic upgrade {{start}}:{{end}} --sql > migration.sql

# Apply pending migrations inside the running API container
[group('database')]
db-upgrade-docker:
    docker exec remote-cnc-api bash -c "cd core && uv run alembic upgrade head"

# Seed the database inside the running API container
[group('database')]
db-seed-docker:
    docker exec remote-cnc-api bash -c "uv run python db_seeder.py"

# Backup the database from the running PostgreSQL container (outputs to db_backup.sql)
[group('database')]
db-backup:
    docker exec -i remote-cnc-postgresql pg_dump -U $DB_USER $DB_NAME > db_backup.sql

# Execute a SQL script against the running PostgreSQL container — usage: just db-execute-script path/to/script.sql
[group('database')]
db-execute-script script:
    docker exec -i remote-cnc-postgresql psql -U $DB_USER --dbname=$DB_NAME < {{script}}

# ===========================================================================
# Docker
# ===========================================================================

# Start API + infra services (no worker)
[group('docker')]
docker-up:
    docker compose up -d

# Start everything including simulated worker (GRBL simulator)
[group('docker')]
docker-up-sim:
    docker compose --profile simulator up -d

# Stop all containers
[group('docker')]
docker-down:
    docker compose down

# Rebuild Docker images
[group('docker')]
docker-build:
    docker compose build

# Tail logs of all containers
[group('docker')]
docker-logs:
    docker compose logs -f

# Open a shell inside the running API container
[group('docker')]
docker-shell:
    docker compose exec api /bin/bash

# Initiate the virtual serial port inside the simulator worker container
[group('docker')]
docker-simport:
    docker exec -it remote-cnc-worker-sim /bin/bash simport.sh

# ===========================================================================
# Deploy
# ===========================================================================

# Create the multi-architecture buildx builder (run once)
[group('deploy')]
deploy-create-builder:
    docker buildx create --name raspberry --driver=docker-container

# Build and push multi-arch API image — usage: just deploy-api <dockerhub_user>
[group('deploy')]
deploy-api user:
    docker buildx build --platform linux/arm/v7,linux/amd64 --tag {{user}}/cnc-api:latest --builder=raspberry --target production --push .

# Build and push multi-arch worker image — usage: just deploy-worker <dockerhub_user>
[group('deploy')]
deploy-worker user:
    docker buildx build --platform linux/arm/v7,linux/amd64 --tag {{user}}/cnc-worker:latest --builder=raspberry --target production --file src/Dockerfile.worker --push src

# ===========================================================================
# Cleanup
# ===========================================================================

# Remove compiled files, caches, logs and coverage reports
[group('cleanup')]
clean:
    uv run python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"
    uv run python -Bc "import pathlib; [p.rmdir() for p in pathlib.Path('.').rglob('__pycache__')]"
    uv run python -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*_cache')]"
    uv run python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.log')]"
    uv run python -Bc "import pathlib; import shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('htmlcov')]"
    uv run python -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('.coverage')]"
