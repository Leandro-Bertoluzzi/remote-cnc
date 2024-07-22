# Deployment (Raspberry Pi)

## Overview

1. Introduction.
1. Update Qt app.
1. Update Docker containers.
1. Database migration.
1. Update CNC worker.

# Introduction

In case you want to deploy to a Linux or Windows machine (x86), the steps are the same as in [development](./development.md) but using `requirements.txt` (or `environment.yml`) intead of the development requirements. This guide assumes you want to install and use the app in a Raspberry Pi.

The steps described in this guide were tested in the following device:
- **Board:** Raspberry Pi 3B+
- **OS:** Raspberry Pi OS (Bullseye, 32-bit)

# Update Qt app

## Copy files to remote

In case you want to use just the strictly necessary files, the needed files and folders to run the app in production are:

- components
- containers
- core
- helpers
- views
- config.py
- docker-compose.yml
- main.py
- MainWindow.py
- rpi/requirements.txt

You can copy them by using [rsync](https://www.raspberrypi.com/documentation/computers/remote-access.html#using-rsync) or a FTP client like [FileZilla](https://docs.digitalocean.com/products/droplets/how-to/transfer-files/).

## Update requirements

In case you updated the `requirements` file:

```bash
# If you haven't, enter the project folder and activate the environment
$ cd cnc-local-app
$ source venv/bin/activate

# Install the missing or new requirements
$ pip install -r rpi/requirements.txt
```

# Update Docker containers

1. If not logged, log in to your Docker account:
```bash
$ docker login
```

2. In the server, stop, update and restart the project in production mode:

```bash
$ cd ~/cnc-local-app
$ docker compose -f docker-compose.yml -f docker-compose.production.yml stop
$ docker compose -f docker-compose.yml -f docker-compose.production.yml rm -f
$ docker compose -f docker-compose.yml -f docker-compose.production.yml pull
$ docker compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

# Database migration

1. Generate a SQL script for the migration following [these steps](./db-management.md#generate-sql-from-migrations-development).

2. You can execute the migration script in production with the `adminer` service, or copy it to the Raspberry and follow [these steps](./db-management.md#execute-a-sql-script).

# Update CNC worker

## Build and push a multi-architecture Docker image

If we have made changes to the code, we must generate a Docker image for the architecture of the Raspberry (ARM 32 v7) before starting our environment with `docker compose up`. The easiest method to achieve that is by [using buildx](https://docs.docker.com/build/building/multi-platform/#multiple-native-nodes).

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
