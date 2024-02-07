# Set up app in production

In case you want to deploy to a Linux or Windows machine (x86), the steps are the same as in [development](./development.md) but using `requirements.txt` (or `conda/environment-prod.yml`) intead of the development requirements. This guide assumes you want to install and use the app in a Raspberry Pi.

The steps described in this guide were tested in the following device:
- **Board:** Raspberry Pi 3B+
- **OS:** Raspberry Pi OS (Bullseye, 32-bit)

## Copy files to remote

In case you want to use just the strictly necessary files, the needed files and folders to run the app in production are:

- components
- containers
- core
- views
- config.py
- docker-compose.yml
- main.py
- MainWindow.py
- rpi/db_schema.sql
- rpi/requirements.txt

**NOTE:** A `requirements.txt` file ready to install in Raspberry Pi OS is in `rpi/requirements.txt`, and that is the one you should use.

## Install dependencies

Before using the app for the first time you should run:

```bash
# Clone this project (unless you manually copied the files)
$ git clone --recurse-submodules https://github.com/Leandro-Bertoluzzi/cnc-local-app

# 1. Access the repository
$ cd cnc-local-app

# 2. Install the needed global site-packages
$ sudo apt-get update
$ sudo apt-get install python3-pyqt5
$ sudo apt-get install python3-pyqt5.qtsvg
$ sudo apt-get install libpq5

# 3. Set up your Python environment
$ python -m venv --system-site-packages venv
$ source venv/bin/activate
$ pip install -r rpi/requirements.txt

# 4. Copy and configure the .env file
cp .env.example .env
```

## Initiate additional required services

In case you don't have (or don't want to use) a DB and a message broker for Celery, you can start a containerized version of both, plus an `adminer` instance, via `docker compose`.

```bash
$ docker compose up -d
```

## Set up database

Once opened the connection with the DB, you must update its schema by running the file `rpi/db_schema.sql`. You can run it with `adminer`.

# Start the app

## Run the Qt app

Once installed all dependencies and created the Python environment, every time you want to start the app you must run:

```bash
# 1. Activate your Python environment
$ source venv/bin/activate

# 2. Start the app
$ python main.py
```

## Start the Celery worker

In order to execute tasks and scheduled tasks, you must start the CNC worker (Celery).

```bash
# 1. Move to worker folder
$ cd core/worker

# 2. Start Celery's worker server
$ celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log
```
