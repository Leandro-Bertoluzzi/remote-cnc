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
$ just start api
```

Open [http://localhost:8000](http://localhost:8000) with your browser to see the result.

## Architecture

The API is an inbound adapter of the Manager application. Its deployment-specific
composition root lives under `src/apps/api/`:

```text
src/
├── apps/api/                 # FastAPI startup, configuration and wiring
├── manager/
│   ├── manager/adapters/api/ # Routes, schemas, middleware and API context
│   └── manager/application/  # CNC Management application services
├── core/                     # Shared domain model and ports
└── infrastructure/           # Concrete outbound adapters
```

`apps.api.context.create_app_context()` selects and injects infrastructure
implementations. API routes receive the Manager context and delegate business
operations to application services; they must not instantiate repositories,
Redis clients or Celery clients directly.

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
