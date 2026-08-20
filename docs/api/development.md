# Development

## Overview

1. [Install dependencies](#install-dependencies).
1. [Run the API locally](#run-the-api-locally).
1. [Run tests](#run-tests).

> **Requirements:** [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just) must be installed.

# Install dependencies

Before using the app for the first time you should run:

```bash
# Clone this project
$ git clone https://github.com/Leandro-Bertoluzzi/remote-cnc

# 1. Access the repository folder
$ cd remote-cnc

# 2. Install all workspace dependencies
$ just sync

# 3. Copy and configure the .env file
$ cp .env.example .env
```

## Environment variables

To complete the environment variables, you must create a `TOKEN_SECRET`. You can run the python interpreter, run the following code and copy the result in the .env file:
```python
from secrets import token_hex
token_hex(64)
```

# Run the API locally

Once dependencies are installed, you can run the API locally with auto-reload:

```bash
$ just start-api
```

Open [http://localhost:8000](http://localhost:8000) with your browser to see the result.

# Run tests

### Unit tests

```bash
$ just test api
```

The coverage report is available in the folder `htmlcov/`.

### Code style linter

```bash
$ just lint
```

### Type check

```bash
$ just typecheck
```
