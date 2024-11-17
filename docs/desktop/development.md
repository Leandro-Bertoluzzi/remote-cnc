# Development

## Overview

1. [Install dependencies](#install-dependencies).
1. [Run the Qt app](#run-the-app).
1. [Run tests](#run-tests).

# Install dependencies

Before using the app for the first time you should run:

```bash
# Clone this project
$ git clone https://github.com/Leandro-Bertoluzzi/remote-cnc

# 1. Access the repository and folder
$ cd remote-cnc/src

# 2. Set up your Python environment
# Option 1: If you use Conda
conda env create -f conda/environment-dev.yml
conda activate remote-cnc-dev

# Option 2: If you use venv and pip
$ python -m venv env-dev
$ source env-dev/bin/activate
$ pip install -r requirements-dev.txt

# 3. Copy and configure the .env file
cp .env.example .env

# 4. Ask git to stop tracking configuration files
$ git update-index --assume-unchanged desktop/config.ini
```

### Windows

Take into account that the virtual environment activation with pip (step 2, option 2) is slightly different in Windows:

```bash
$ python -m venv env-dev
$ .\env-dev\Scripts\activate
$ pip install -r requirements-dev.txt
```

# Run the app

Once installed all dependencies and created the Python environment, every time you want to start the app you must run:

```bash
# 1. Activate your Python environment
# Option 1: If you use Conda
conda activate remote-cnc-dev

# Option 2: If you use venv and pip
$ source env-dev/bin/activate

# 2. Start the app with auto-reload
$ watchmedo auto-restart --directory=./ --pattern=*.py --recursive --  python main.py
```

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
