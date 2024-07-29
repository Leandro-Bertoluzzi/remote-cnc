# Development

## Overview

1. [Install dependencies](#install-dependencies).
1. [Run the API locally](#run-the-api-locally).
1. [Run tests](#run-tests).

# Install dependencies

Before using the app for the first time you should run:

```bash
# Clone this project
$ git clone https://github.com/Leandro-Bertoluzzi/remote-cnc

# 1. Access the repository and folder
$ cd remote-cnc/api

# 2. Set up your Python environment
# Option 1: If you use Conda
conda env create -f environment.yml
conda activate cnc-remote-api

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ source env-dev/bin/activate
$ pip install -r requirements-dev.txt

# 3. Ask pip to install local packages in development mode
# This is needed to use 'core' as a package in local development
pip install -e .

# 4. Copy and configure the .env files
cp .env.example .env
cp core/.env.example core/.env
```

### Windows

Take into account that the virtual environment activation with pip (step 2, option 2) is slightly different in Windows:

```bash
$ python -m venv env-dev
$ .\env-dev\Scripts\activate
$ pip install -r requirements-dev.txt
```

## Environment variables

To complete the environment variables, you must create a `TOKEN_SECRET`. You can run the python interpreter, run the following code and copy the result in the .env file:
```python
from secrets import token_hex
token_hex(64)
```

# Run the API locally

Once installed all dependencies and created the Python environment, you can run the API locally:

```bash
# 1. Activate your Python environment
# Option 1: If you use Conda
conda activate cnc-remote-api

# Option 2: If you use venv and pip
$ source env-dev/bin/activate

# 2. Start the app with auto-reload
$ uvicorn app:app --reload
```

Open [http://localhost:8000](http://localhost:8000) with your browser to see the result.

# Run tests

If you are using Docker, you'll have to enter the container first:
```bash
$ docker compose exec -it api /bin/bash
```

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
