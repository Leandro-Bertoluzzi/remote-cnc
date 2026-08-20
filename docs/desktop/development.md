# Development

## Overview

1. [Install dependencies](#install-dependencies).
1. [Run the Qt app](#run-the-app).
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

# 4. Copy and configure the desktop config file
$ cp desktop/config.ini.example src/desktop/desktop/config.ini
```

# Run the app

Once dependencies are installed, every time you want to start the app run:

```bash
# Start the app
$ just start-desktop

# Or start with auto-reload on file changes
$ just start-desktop-watch
```

## Start additional services

The desktop app connects to the backend services (API, PostgreSQL, Redis, Worker). Start them with Docker:

```bash
$ just compose-up-dev
```

### Linux: fix folder permissions after first Docker run

Docker creates the `gcode_files/`, `thumbnails/`, and `logs/` folders as root when mounting volumes for the first time. If the desktop app raises a `PermissionError` when trying to read or write files, restore ownership with:

```bash
$ just fix-permissions
```

# Run tests

### Unit tests

```bash
$ just test desktop
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
