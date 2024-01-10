<h1 align="center">CNC manager core</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/Leandro-Bertoluzzi/cnc-admin-core?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/Leandro-Bertoluzzi/cnc-admin-core?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/Leandro-Bertoluzzi/cnc-admin-core?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/Leandro-Bertoluzzi/cnc-admin-core?color=56BEB8">
</p>

<!-- Status -->

<h4 align="center">
	🚧 CNC manager core 🚀 Under construction...  🚧
</h4>

<hr>

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0;
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Authors</a>
</p>

<br>

## :dart: About

Core application code to monitor and manage an Arduino-based CNC machine connected to the local machine.

## :sparkles: Features

:heavy_check_mark: PostgreSQL database management\
:heavy_check_mark: G-code files management\
:heavy_check_mark: Real time monitoring of CNC status\
:heavy_check_mark: Communication with GRBL-compatible CNC machine via USB\
:heavy_check_mark: Long-running process delegation via message broker

## :rocket: Technologies

The following tools were used in this project:

-   [Python](https://www.python.org/)
-   [PostgreSQL](https://www.postgresql.org/)
-   [SQLAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/en/latest/)
-   [Celery](https://docs.celeryq.dev/en/stable/)
-   [Redis](https://redis.io/)
-   [Docker](https://www.docker.com/)

## :white_check_mark: Requirements

Before starting :checkered_flag:, you need to have [Python](https://www.python.org/) installed.

## :checkered_flag: Development

### Linux

```bash
# Clone this project
$ git clone https://github.com/Leandro-Bertoluzzi/cnc-admin-core

# 1. Access the repository
$ cd cnc-admin-core

# 2. Set up your Python environment
# Option 1: If you use Conda
conda env create -f environment.yml
conda activate cnc-admin-core

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ source env/bin/activate
$ pip install -r requirements-dev.txt

# 3. Copy and configure the .env file
cp .env.example .env

# 4. Run Docker to start the DB, PHPMyAdmin, the
# CNC worker (Celery) and its Message broker (Redis)
$ docker compose -f docker-compose.yml -f docker-compose.worker.yml up -d

# 5. If you are starting a new DB, run DB migrations
$ alembic upgrade head
```

### Windows

If you are developing on Windows, the file `docker-compose.worker.yml` won't work since **_devices_** is not able to map Windows ports to Linux containers. Options are:

1. Use a virtual machine with a Linux distribution.
2. Run `docker-compose up` (without the worker) and start the worker manually.
3. Don't use docker-compose at all and start all services the usual way, or with `docker run` (see [Deployment](#deployment) section for more information).

If you choose the option 2, you shall follow the following steps:

```bash
# Clone this project
$ git clone https://github.com/Leandro-Bertoluzzi/cnc-admin-core

# 1. Access the repository
$ cd cnc-admin-core

# 2. Set up your Python environment
# Option 1: If you use Conda
$ conda env create -f environment-dev.yml
$ conda activate cnc-admin-core
$ conda install -c anaconda gevent

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ .\env\Scripts\activate
$ pip install -r requirements-dev.txt
$ pip install gevent

# 3. Copy and configure the .env file
cp .env.example .env

# 4. Run Docker to start the DB, PHPMyAdmin and the Message broker (Redis)
$ docker compose up -d

# 5. If you are starting a new DB, run DB migrations
$ alembic upgrade head

# 6. Start the Celery worker
$ cd worker
$ celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log --pool=gevent
```

## :wrench: Running tests

### Unit tests

```bash
$ pytest -s --cov-config=setup.cfg
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

## :memo: License

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.

## :writing_hand: Authors

Made with :heart: by <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Leandro Bertoluzzi</a> and Martín Sellart.

<a href="#top">Back to top</a>
