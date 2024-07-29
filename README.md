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
  <a href="#checkered_flag-installation">Installation</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-development">Development</a> &#xa0; | &#xa0;
  <a href="#rocket-deploy-changes">Deploy changes</a> &#xa0; | &#xa0;
  <a href="#gear-cnc-worker">CNC worker</a>
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Authors</a>
</p>

<br>

## :dart: About

This repository comprises two related applications:
- **Desktop**: A small desktop app to monitor and control an Arduino-based CNC machine.
- **API**: REST API to integrate the app's functionalities in a remote client.

You can see further information in their respective folders.

## :sparkles: Features

:heavy_check_mark: REST API\
:heavy_check_mark: Desktop app, optimized for touchscreen

## :checkered_flag: Installation

Each subproject's folder contains instructions to start using them in production:
- Desktop: See installation docs for desktop app [here](./desktop/docs/installation.md).
- API: See installation docs for API [here](./api/docs/server-setup.md).

### Set up database

You can execute the script `rpi/db_schema.py` in production with the `adminer` service, or copy it to the Raspberry and follow [these steps](rpi/db-management.md#execute-a-sql-script).

## :checkered_flag: Development

The easiest way to run the needed services is with `Docker`. This will start the API and the following services:
- PostgreSQL DB.
- Adminer, to manage the DB.
- Message broker (Redis).
- Flower, to monitor the Celery worker.

```bash
$ docker compose up -d
```

if you want to also start the CNC worker (Celery) in a container (Linux only, see [this section](#cnc-worker)):
```bash
$ docker compose --profile=worker up -d
```

Open [http://localhost:8000](http://localhost:8000) with your browser to check if the API works.

You can find instructions to run locally (without Docker) and further information in each subproject's folder:
- Desktop: See development docs for desktop app [here](./desktop/docs/development.md).
- API: See development docs for API [here](./api/docs/development.md).

### Mock external services

In addition, you can also add a mocked version of the GRBL device, which runs the [GRBL simulator](https://github.com/grbl/grbl-sim).

```bash
$ docker compose -f docker-compose.yaml -f docker-compose.test.yaml up
```

For the worker/app to use the mocked port, update your environment (or ini file) to use a virtual port:

```bash
SERIAL_PORT=/dev/ttyUSBFAKE
```

Initiate the virtual port inside the worker's container:

```bash
docker exec -it remote-cnc-worker /bin/bash simport.sh
```

### Manage database

To see your database, you can either use the `adminer` container which renders an admin in `http://localhost:8080` when running the `docker-compose.yaml`; or connect to it with a client like [DBeaver](https://dbeaver.io/).

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

if you are using `docker compose`, you can run the following commands to apply database migrations and seed it:

```bash
$ docker exec remote-cnc-api bash -c "cd core && alembic upgrade head"
$ docker exec remote-cnc-api bash -c "cd core && python seeder.py"
```

## :rocket: Deploy changes

Each subproject's folder contains instructions to deploy changes to production:
- Desktop: See deployment docs for desktop app [here](./desktop/docs/deployment.md).
- API: See deployment docs for API [here](./api/docs/deployment.md).

### Update Docker containers

If we modify the Docker image for the API or Worker, or we just need to update the version of one of the other services, we have to follow the next steps.

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

**NOTE:** Take into account that you may add `--profile=worker` to each command above if you are using the `worker` service. The same applies for other optional services (ngrok).

### Database migrations

1. Generate a SQL script for the migration following [these steps](rpi/db-management.md#generate-sql-from-migrations-development).
1. You can either execute the migration script in production with the `adminer` service, or copy it to the Raspberry and follow [these steps](rpi/db-management.md#execute-a-sql-script).

### Update CNC worker Docker image

If you are using the `worker` service and you have made changes to the code, you must generate a Docker image for the architecture of the Raspberry (ARM 32 v7), to pull it in production. The easiest method to achieve that is by [using buildx](https://docs.docker.com/build/building/multi-platform/#multiple-native-nodes).

**The first time** we generate the image, we must create a custom builder.

```bash
docker buildx create --name raspberry --driver=docker-container
```

Then, the command to actually generate the image and update the remote repository is the following:

```bash
docker buildx build --platform linux/arm/v7,linux/amd64 --tag {{your_dockerhub_user}}/cnc-worker:latest --builder=raspberry --target production --file core/Dockerfile.worker --push core
```

**NOTE:** You may have to log in with `docker login` previous to run the build command.

Then, follow the guide to [update Docker containers](#update-docker-containers) in the Raspberry.

## :gear: CNC worker

The CNC worker should start automatically when running `docker compose --profile=worker up`, with certain conditions:

- It only works with Docker CE without Docker Desktop, because the latter can't mount devices. You can view a discussion about it [here](https://forums.docker.com/t/usb-devices-mapping-not-works-with-docker-desktop/132148).
- Therefore, and given that devices in Windows work in a completely different way (there is no `/dev` folder), you won't be able to run the `worker` service on Windows. For that reason, in Windows you'll have to follow the steps in [Start the Celery worker manually (Windows)](#start-the-celery-worker-manually-windows).

### Start the Celery worker manually (Linux)

In case you don't use Docker or just want to run it manually, you can follow the next steps.

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

### Start the Celery worker manually (Windows)

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

## :wrench: Running tests

You can use the following commands to execute tests (unit, linter, type check) in any of the folders:
```bash
$ make test-api
$ make test-core
$ make test-desktop
```

## :memo: License

This project is under license from MIT. For more details, see the [LICENSE](LICENSE.md) file.

## :writing_hand: Authors

Made with :heart: by <a href="https://github.com/Leandro-Bertoluzzi" target="_blank">Leandro Bertoluzzi</a> and Martín Sellart.

<a href="#top">Back to top</a>
