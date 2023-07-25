<h1 align="center">CNC worker</h1>

## :dart: About ##

Task manager module to run long-running and/or asynchronous processes in the background to manage communication with the CNC machine, according to instructions delegated by another program via a message broker.

## :white_check_mark: Requirements ##

Before starting :checkered_flag:, you need to have [Python](https://www.python.org/) installed and either [Redis](https://redis.io/) or [Docker](https://www.docker.com/).

## :checkered_flag: Development ##

In order to run this module alone, you should follow the following steps, which depend on which OS you are using.

- Linux/Mac:

```bash
# Set up your Python environment
# Option 1: If you use Conda
conda env create -f environment.yml
conda activate cnc-task-manager

# Option 2: If you use venv and pip
$ pip install -r requirements.txt
$ python -m venv env
$ source tutorial-env/bin/activate

# Start the Redis server, you can achieve this with Docker:
$ docker run -d -p 6379:6379 redis

# Start Celery's worker server
$ celery --app tasks worker --loglevel=INFO
```

- Windows:

```bash
# Set up your Python environment
# Option 1: If you use Conda
conda env create -f environment-windows.yml
conda activate cnc-task-manager

# Option 2: If you use venv and pip
$ pip install -r requirements-windows.txt
$ python -m venv env
# run the script: env\Scripts\activate.bat

# Start the Redis server
$ docker run -d -p 6379:6379 redis

# Start Celery's worker server
$ celery --app tasks worker --loglevel=INFO --pool=gevent
```

You can see an explanation on how to run Celery 4+ on Windows here: [link](https://distributedpython.com/posts/two-ways-to-make-celery-4-run-on-windows/).

- Docker compose:

Optionally, you can use the docker-compose.yml file to start both the Redis MQ and the Celery worker, in which case you'll have to run:

```bash
$ docker-compose up
```
