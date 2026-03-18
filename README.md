<h1 align="center">CNC admin</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/Leandro-Bertoluzzi/remote-cnc?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/Leandro-Bertoluzzi/remote-cnc?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/Leandro-Bertoluzzi/remote-cnc?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/Leandro-Bertoluzzi/remote-cnc?color=56BEB8">
</p>

<!-- Status -->

<h4 align="center">
	🚧 CNC admin 🚀 Under construction...  🚧
</h4>

<hr>

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-installation">Installation</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-development">Development</a> &#xa0; | &#xa0;
  <a href="#rocket-deploy-changes">Deploy changes</a> &#xa0; | &#xa0;
  <a href="#gear-cnc-gateway">CNC gateway</a> &#xa0; | &#xa0;
  <a href="#gear-cnc-worker">CNC worker</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Authors</a>
</p>

<br>

## :dart: About

This repository comprises the following components:

- **Desktop**: A small desktop app to monitor and control an Arduino-based CNC machine, optimized for touchscreen.
- **API**: REST API to integrate the app's functionalities in a remote client.
- **Gateway**: Long-running process that manages serial communication with the CNC device.
- **Worker**: Celery background worker for long-running tasks (e.g. file execution, thumbnail generation).

## :sparkles: Features

:heavy_check_mark: PostgreSQL database management\
:heavy_check_mark: G-code files management\
:heavy_check_mark: Real time monitoring of CNC status\
:heavy_check_mark: Communication with GRBL-compatible CNC machine via USB\
:heavy_check_mark: Long-running process delegation via message broker

## :rocket: Technologies

The following tools were used in this project:

- Programming language: [Python](https://www.python.org/)
- API framework: [FastAPI](https://fastapi.tiangolo.com/)
- UI (desktop) framework: [PyQt](https://wiki.python.org/moin/PyQt)
- Database: [PostgreSQL](https://www.postgresql.org/)
- ORM: [SQLAlchemy](https://www.sqlalchemy.org/)
- DB migrations: [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- Tasks queue: [Celery](https://docs.celeryq.dev/en/stable/)
- Message broker: [Redis](https://redis.io/)
- Containerization: [Docker](https://www.docker.com/)

## :white_check_mark: Requirements

Before starting :checkered_flag:, you need to have [Python](https://www.python.org/), [uv](https://docs.astral.sh/uv/) and [Docker](https://www.docker.com/) installed.

Optionally, install [just](https://just.systems/) to use the project's command runner (`justfile`). See the [available recipes](#available-recipes) for a full reference.

## :checkered_flag: Installation

There is a folder for each subproject in docs, which contain instructions to start using them in production:

- Desktop: See installation docs for desktop app [here](docs/desktop/installation.md).
- API: See installation docs for API [here](docs/api/server-setup.md).

### Set up database

You can copy the script `deployment/db_schema.py` to the Raspberry and follow [these steps](docs/db/db-management.md#execute-a-sql-script).

## :checkered_flag: Development

### Project structure

This is a **uv workspace** monorepo. All Python source lives under `src/`:

```text
src/
├── pyproject.toml          # Workspace root (virtual)
├── uv.lock                 # Single lockfile for the whole workspace
├── core/                   # Shared library: database, config, utilities, schemas
│   ├── pyproject.toml
│   ├── core/               # Python package
│   ├── alembic/            # Database migrations
│   └── alembic.ini
├── api/                    # FastAPI REST API
│   ├── pyproject.toml
│   ├── main.py             # Entry point
│   ├── routes/
│   ├── middleware/
│   └── tests/
├── worker/                 # Celery background worker
│   ├── pyproject.toml
│   ├── main.py             # Entry point
│   ├── tasks/
│   └── tests/
├── gateway/                # CNC gateway (serial communication)
│   ├── pyproject.toml
│   └── gateway/            # Python package
├── desktop/                # PyQt5 desktop application
│   ├── pyproject.toml
│   ├── main.py             # Entry point
│   ├── views/
│   ├── components/
│   └── tests/
└── tests/                  # Core / shared tests + mocks
    ├── conftest.py
    └── mocks/
```

### Available recipes

The `justfile` at the root of the repository contains all common development and operations commands, organised by group. Run `just` (no arguments) to see the full list at any time.

> `*` Requires Docker containers to be running.

| Recipe                                | Group    | Description                                   |
| ------------------------------------- | -------- | --------------------------------------------- |
| `sync`                                | setup    | Install / update deps from lockfile           |
| `lock`                                | setup    | Re-resolve & update `uv.lock`                 |
| `test`                                | quality  | Run all tests                                 |
| `test-core`                           | quality  | Core / shared tests                           |
| `test-api`                            | quality  | API tests                                     |
| `test-worker`                         | quality  | Worker tests                                  |
| `test-desktop`                        | quality  | Desktop tests                                 |
| `lint`                                | quality  | Run linter                                    |
| `lint-fix`                            | quality  | Run linter with auto-fix                      |
| `format`                              | quality  | Run formatter                                 |
| `typecheck`                           | quality  | Run type checker                              |
| `check`                               | quality  | lint + typecheck + test                       |
| `start-api`                           | run      | Start the API with uvicorn (dev)              |
| `start-desktop`                       | run      | Start the desktop (PyQt5) app                 |
| `start-desktop-watch`                 | run      | Desktop app with auto-reload                  |
| `start-worker`                        | run      | Start the Celery worker                       |
| `start-worker-watch`                  | run      | Celery worker with auto-reload                |
| `db-upgrade`                          | database | Apply pending migrations (local)              |
| `db-downgrade`                        | database | Revert last migration (local)                 |
| `db-revision <msg>`                   | database | Auto-generate a new migration                 |
| `db-seed`                             | database | Seed the database (local)                     |
| `db-generate-schema`                  | database | Export full schema as SQL                     |
| `db-generate-migration <start> <end>` | database | Export SQL for a migration range              |
| `db-upgrade-docker` `*`               | database | Apply migrations in the API container         |
| `db-seed-docker` `*`                  | database | Seed the database in the API container        |
| `db-backup` `*`                       | database | Backup DB from the PostgreSQL container       |
| `db-execute-script <path>` `*`        | database | Run a SQL script against the DB container     |
| `docker-up`                           | docker   | Start API + worker + infra                    |
| `docker-up-dev`                       | docker   | Start everything + simulated CNC gateway      |
| `docker-down`                         | docker   | Stop all containers                           |
| `docker-build`                        | docker   | Rebuild Docker images                         |
| `docker-logs`                         | docker   | Tail logs of all containers                   |
| `docker-shell` `*`                    | docker   | Open a shell in the API container             |
| `deploy-create-builder`               | deploy   | Create multi-arch buildx builder (once)       |
| `deploy-api <user>`                   | deploy   | Build & push multi-arch API image             |
| `deploy-worker <user>`                | deploy   | Build & push multi-arch worker image          |
| `deploy-gateway <user>`               | deploy   | Build & push multi-arch gateway image         |
| `clean`                               | cleanup  | Remove compiled files, caches, logs, coverage |

### First-time setup

```bash
# 1. Clone the repository
$ git clone https://github.com/Leandro-Bertoluzzi/remote-cnc.git
$ cd remote-cnc

# 2. Copy and fill in environment variables
$ cp .env.example .env

# 3. Install all dependencies (creates a single virtualenv for the workspace)
$ just sync
```

### Running with Docker (recommended)

The easiest way to run the needed services is with `Docker`. This will start the API, the Celery worker, and the following services:

- PostgreSQL DB.
- Message broker (Redis).
- Flower, to monitor the Celery worker.

```bash
$ just docker-up
```

If you want to also start the CNC gateway to connect a physical CNC device (Linux only, see [this section](#gear-cnc-gateway)):

```bash
$ docker compose --profile=device up -d
```

Open [http://localhost:8000](http://localhost:8000) with your browser to check if the API works.

### Running locally (without Docker)

```bash
# Start the API
$ just start-api

# Start the desktop app
$ just start-desktop

# Start the Celery worker
$ just start-worker
```

You can find further information in each subproject's docs folder:

- Desktop: See development docs for desktop app [here](docs/desktop/development.md).
- API: See development docs for API [here](docs/api/development.md).

### Mock external services

You can also run a gateway with a mocked version of the GRBL device, which runs the [GRBL simulator](https://github.com/grbl/grbl-sim).
**NOTE:** This also works on Windows, since the simulated gateway doesn't need USB device access.

```bash
$ docker compose --profile=simulator up
```

The simulated gateway automatically creates the virtual serial port on startup using the GRBL simulator. Make sure your environment has the following variable set:

```bash
SERIAL_PORT=/dev/ttyUSBFAKE
```

### Manage database

To see your database, you can connect to it with a client like [DBeaver](https://dbeaver.io/).

You can manage database migrations with the following `just` recipes (which wrap Alembic commands):

- Apply all migrations:

```bash
$ just db-upgrade
```

- Revert last migration:

```bash
$ just db-downgrade
```

- Auto-generate a new revision:

```bash
$ just db-revision "add users table"
```

- Seed DB with initial data:

```bash
$ just db-seed
```

More info about Alembic usage [here](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

If you are using `docker compose`, you can apply migrations and seed the database without entering the container:

```bash
$ just db-upgrade-docker
$ just db-seed-docker
```

## :rocket: Deploy changes

There is a folder for each subproject in docs, which contain instructions to deploy changes to production:

- Desktop: See deployment docs for desktop app [here](docs/desktop/deployment.md).
- API: See deployment docs for API [here](docs/api/deployment.md).

### Update Docker containers

If we modify the Docker image for the API, Worker, or Gateway, or we just need to update the version of one of the other services, we have to follow the next steps.

1. If not logged, log in to your Docker account:

```bash
$ docker login
```

2. In the server, stop, update and restart the project in production mode:

```bash
$ cd /home/username/adminapp
$ docker compose -f docker-compose.yaml -f docker-compose.production.yaml stop
$ docker compose -f docker-compose.yaml -f docker-compose.production.yaml rm -f
$ docker compose -f docker-compose.yaml -f docker-compose.production.yaml pull
$ docker compose -f docker-compose.yaml -f docker-compose.production.yaml up -d
```

**NOTE:** Take into account that you may add `--profile=device` to each command above if you are using the CNC `gateway` service. The same applies for other optional services (ngrok).

### Database migrations

1. Generate a SQL script for the migration following [these steps](rpi/db-management.md#generate-sql-from-migrations-development).
1. You can copy the migration script to the Raspberry and follow [these steps](rpi/db-management.md#execute-a-sql-script).

### Update CNC worker Docker image

If you have made changes to the worker code, you must generate a Docker image for the architecture of the Raspberry (ARM 32 v7), to pull it in production. The easiest method to achieve that is by [using buildx](https://docs.docker.com/build/building/multi-platform/#multiple-native-nodes).

**The first time** we generate the image, we must create a custom builder.

```bash
docker buildx create --name raspberry --driver=docker-container
```

Then, the command to actually generate the image and update the remote repository is the following:

```bash
docker buildx build --platform linux/arm/v7,linux/amd64 --tag {{your_dockerhub_user}}/cnc-worker:latest --builder=raspberry --target production --file src/Dockerfile.worker --push src
```

**NOTE:** You may have to log in with `docker login` previous to run the build command.

Then, follow the guide to [update Docker containers](#update-docker-containers) in the Raspberry.

### Update CNC gateway Docker image

Similarly, if you have made changes to the gateway code, generate a multi-arch image:

```bash
docker buildx build --platform linux/arm/v7,linux/amd64 --tag {{your_dockerhub_user}}/cnc-gateway:latest --builder=raspberry --target production --file src/Dockerfile.gateway --push src
```

Then, follow the guide to [update Docker containers](#update-docker-containers) in the Raspberry.

## :gear: CNC gateway

The CNC gateway manages serial communication with the physical CNC device. It should start automatically when running `docker compose --profile=device up`, with certain conditions:

- It only works with Docker CE without Docker Desktop, because the latter can't mount devices. You can view a discussion about it [here](https://forums.docker.com/t/usb-devices-mapping-not-works-with-docker-desktop/132148).
- Therefore, and given that devices in Windows work in a completely different way (there is no `/dev` folder), you won't be able to run the `gateway` service on Windows. For that reason, in Windows you can use the [simulated gateway](#mock-external-services) instead.

## :gear: CNC worker

### Start the Celery worker manually (Linux)

In case you don't use Docker or just want to run it manually, you can follow the next steps.

```bash
# Start Celery's worker server
$ just start-worker
```

Optionally, if you are going to make changes in the worker's code and want to see them in real time, you can start the Celery worker with auto-reload.

```bash
$ cd src && uv run watchmedo auto-restart --directory=./ --pattern=*.py -- celery --app worker.main worker --loglevel=INFO --logfile=logs/celery.log
```

### Start the Celery worker manually (Windows)

Due to a known problem with Celery's default pool (prefork), it is not as straightforward to start the worker in Windows. In order to do so, we have to explicitly indicate Celery to use another pool. You can read more about this issue [here](https://celery.school/celery-on-windows).

- **solo**: The solo pool is a simple, single-threaded execution pool. It simply executes incoming tasks in the same process and thread as the worker.

```bash
$ cd src && uv run celery --app worker.main worker --loglevel=INFO --logfile=logs/celery.log --pool=solo
```

- **threads**: The threads in the threads pool type are managed directly by the operating system kernel. As long as Python's ThreadPoolExecutor supports Windows threads, this pool type will work on Windows.

```bash
$ cd src && uv run celery --app worker.main worker --loglevel=INFO --logfile=logs/celery.log --pool=threads
```

- **gevent**: The [gevent package](http://www.gevent.org/) officially supports Windows, so it remains a suitable option for IO-bound task processing on Windows. Downside is that you have to install it first.

```bash
# 1. Install gevent
$ cd src && uv add gevent

# 2. Start Celery's worker server
$ cd src && uv run celery --app worker.main worker --loglevel=INFO --logfile=logs/celery.log --pool=gevent
```

## :wrench: Running tests

You can use the following commands to execute tests and quality checks:

```bash
# Run all tests
$ just test

# Run tests for a specific service
$ just test-core
$ just test-api
$ just test-worker
$ just test-desktop

# Run all quality checks (lint + typecheck + test)
$ just check
```

## :memo: License

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.

## :writing_hand: Authors

Made with :heart: by <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Leandro Bertoluzzi</a> and Martín Sellart.

<a href="#top">Back to top</a>
