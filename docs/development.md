# Start development environment

## Linux

The first time you use the app you should run:

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
$ pip install -r pip/requirements-dev.txt

# 3. Copy and configure the .env file
cp .env.example .env

# 4. Run Docker to start the DB, PHPMyAdmin
# and the Message broker (Redis)
$ docker compose up -d

# 5. If you are starting a new DB, run DB migrations
$ cd core
$ alembic upgrade head
```

Then, every time you want to start the app:

```bash
# 1. Activate your Python environment
# Option 1: If you use Conda
conda activate cnc-local-app-dev

# Option 2: If you use venv and pip
$ source env-dev/bin/activate

# 2. Run Docker to start the DB, PHPMyAdmin
# and the Message broker (Redis)
$ docker compose up -d

# 3. Start the app with auto-reload
$ cd ..
$ watchmedo auto-restart --directory=./ --pattern=*.py --recursive --  python main.py
```

## Windows

The first time you use the app you should run:

```bash
# Clone this project
$ git clone --recurse-submodules https://github.com/Leandro-Bertoluzzi/cnc-local-app

# 1. Access the repository
$ cd cnc-local-app

# 2. Set up your Python environment
# Option 1: If you use Conda
conda env create -f conda/environment-dev-windows.yml
conda activate cnc-local-app-dev

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ .\env\Scripts\activate
$ pip install -r pip/requirements-dev-windows.txt
```

After running `docker compose up`, notice the `worker` service won't work since **_devices_** is not able to map Windows ports to Linux containers. Options are:

1. Use a virtual machine with a Linux distribution.
2. Run `docker-compose up` without the worker and start the worker manually.
3. Don't use docker-compose at all and start all services the usual way, or with `docker run` (see [Deployment](./deployment.md) section for more information).

If you choose the option 2, you shall comment the `worker` service in `docker-compose.yml` and follow the following steps:

```bash
# 1. DB, PHPMyAdmin
# and the Message broker (Redis)
$ docker compose up -d

# 2. If you are starting a new DB, run DB migrations
$ cd core
$ alembic upgrade head
$ cd ..

# 3. Start the app with auto-reload
$ watchmedo auto-restart --directory=./ --pattern=*.py --recursive --  python main.py

# 4. Start the Celery worker
# Move to worker folder
$ cd core/worker

# Start Celery's worker server
# Option 1: With auto-reload
$ watchmedo auto-restart --directory=./ --pattern=*.py -- celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log --pool=gevent

# Option 2: Static (in case you won't make changes to the worker)
$ celery --app tasks worker --loglevel=INFO --logfile=logs/celery.log --pool=gevent
```
