# Development

## Overview

1. [Install the Qt app](#install-the-qt-app).
1. [Initiate additional services](#initiate-additional-services).
1. [Mock external services](#mock-external-services)
1. [Manage database](#manage-database).
1. [CNC worker](#cnc-worker).
1. [Run tests](#run-tests).

# Install the Qt app

## Install dependencies

Before using the app for the first time you should run:

```bash
# Clone this project
$ git clone --recurse-submodules https://github.com/Leandro-Bertoluzzi/cnc-local-app

# 1. Access the repository
$ cd cnc-local-app

# 2. Set up your Python environment
# Option 1: If you use Conda
conda env create -f conda/environment-dev.yml
conda activate cnc-local-app-dev

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ source env-dev/bin/activate
$ pip install -r requirements-dev.txt

# 3. Copy and configure the .env file
cp .env.example .env

# 4. Ask git to stop tracking configuration files
$ git update-index --assume-unchanged config.ini
```

### Windows

Take into account that the virtual environment activation with pip (step 2, option 2) is slightly different in Windows:

```bash
$ python -m venv env-dev
$ .\env-dev\Scripts\activate
$ pip install -r requirements-dev.txt
```

## Run the app

Once installed all dependencies and created the Python environment, every time you want to start the app you must run:

```bash
# 1. Activate your Python environment
# Option 1: If you use Conda
conda activate cnc-local-app-dev

# Option 2: If you use venv and pip
$ source env-dev/bin/activate

# 2. Start the app with auto-reload
$ watchmedo auto-restart --directory=./ --pattern=*.py --recursive --  python main.py
```

# Initiate additional services

In case you don't have (or don't want to use) a DB and a message broker for Celery, you can start a containerized version of both, plus an `adminer` instance, via `docker compose`.

```bash
# 1. Run Docker to start the DB, adminer,
# the CNC worker and the Message broker (Redis)
$ docker compose up -d
```

# Mock external services

In addition, you can also add a mocked version of the GRBL device, which runs the [GRBL simulator](https://github.com/grbl/grbl-sim).

```bash
$ docker compose -f docker-compose.yml -f docker-compose.test.yml up
```

## Using GRBL simulator

Update your environment to use a virtual port:

```bash
SERIAL_PORT=/dev/ttyUSBFAKE
```

Initiate the virtual port inside the worker's container:

```bash
docker exec -it cnc-admin-worker /bin/bash simport.sh
```

# Manage database

To see your database, you can either use the `adminer` container which renders an admin in `http://localhost:8080` when running the `docker-compose.yml`; or connect to it with a client like [DBeaver](https://dbeaver.io/).

You can also manage database migrations by using the following commands inside the `core` folder.

- Apply all migrations:

```bash
$ alembic upgrade head
```

- Revert all migrations:

```bash
$ alembic downgrade base
```

- Seed DB with initial data:

```bash
$ python seeder.py
```

More info about Alembic usage [here](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

# CNC worker

The CNC worker should start automatically when running `docker compose up`, with certain conditions:

- It only works with Docker CE without Docker Desktop, because the latter can't mount devices. You can view a discussion about it [here](https://forums.docker.com/t/usb-devices-mapping-not-works-with-docker-desktop/132148).
- Therefore, and given that devices in Windows work in a completely different way (there is no `/dev` folder), you won't be able to run the `worker` service on Windows. For that reason, in Windows you'll have to comment the `worker` service in `docker-compose.yml` and follow the steps in [Start the Celery worker manually (Windows)](#start-the-celery-worker-manually-windows).

## Start the Celery worker manually (Linux)

In case you don't use Docker or just want to run it manually (by commenting the `worker` service in `docker-compose.yml`), you can follow the next steps.

```bash
# 1. Move to worker folder
$ cd core/worker

# 2. Start Celery's worker server
$ celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log
```

Optionally, if you are going to make changes in the worker's code and want to see them in real time, you can start the Celery worker with auto-reload.

```bash
# 1. Move to worker folder
$ cd core/worker

# 2. Start Celery's worker server with auto-reload
$ watchmedo auto-restart --directory=./ --pattern=*.py -- celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log
```

**NOTE:** You also have to update the value of `PROJECT_ROOT` in `config.py`.

## Start the Celery worker manually (Windows)

Due to a known problem with Celery's default pool (prefork), it is not as straightforward to start the worker in Windows. In order to do so, we have to explicitly indicate Celery to use another pool. You can read more about this issue [here](https://celery.school/celery-on-windows).

- **solo**: The solo pool is a simple, single-threaded execution pool. It simply executes incoming tasks in the same process and thread as the worker.

```bash
$ celery --app worker worker --loglevel=INFO --logfile=logs/celery.log --pool=solo
```

- **threads**: The threads in the threads pool type are managed directly by the operating system kernel. As long as Python's ThreadPoolExecutor supports Windows threads, this pool type will work on Windows.

```bash
$ celery --app worker worker --loglevel=INFO --logfile=logs/celery.log --pool=threads
```

- **gevent**: The [gevent package](http://www.gevent.org/) officially supports Windows, so it remains a suitable option for IO-bound task processing on Windows. Downside is that you have to install it first.

```bash
# 1. Install gevent
# Option 1: If you use Conda
$ conda install -c anaconda gevent

# Option 2: If you use pip
$ pip install gevent

# 2. Start Celery's worker server
$ celery --app worker worker --loglevel=INFO --logfile=logs/celery.log --pool=gevent
```

**NOTE:** You also have to update the value of `PROJECT_ROOT` in `config.py`.

# Run tests

### Unit tests

```bash
$ pytest -s
```

The coverage report is available in the folder `/htmlcov`.

### Code style linter

```bash
$ flake8
```

### Type check

```bash
$ mypy .
```

### All tests

You can also run all tests together, by using the following command:

```bash
$ make tests
```
