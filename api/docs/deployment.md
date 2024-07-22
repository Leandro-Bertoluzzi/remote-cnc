# Deploy changes (Raspberry Pi)

## Overview

1. [Introduction](#introduction).
1. [Deploy API](#deploy-api).
1. [Database migrations](#database-migrations).
1. [Update CNC worker](#update-cnc-worker).
1. [Nginx configuration](#nginx-configuration).

# Introduction

This guide assumes you are using the app in a Raspberry Pi and followed the steps in [server setup](./server-setup.md).

The steps described in this guide were tested in the following device:
- **Board:** Raspberry Pi 3B+
- **OS:** Raspberry Pi OS (Bullseye, 32-bit)

# Deploy API

## Build and push a multi-architecture Docker image

If we have made changes to the code, we must generate a Docker image for the architecture of the Raspberry (ARM 32 v7) before starting our environment with `docker compose up`. The easiest method to achieve that is by [using buildx](https://docs.docker.com/build/building/multi-platform/#multiple-native-nodes).

**The first time** we generate the image, we must create a custom builder.

```bash
docker buildx create --name raspberry --driver=docker-container
```

Then, the commands to actually generate the images and update the remote repository are the following:

```bash
docker buildx build --platform linux/arm/v7,linux/amd64 --builder=raspberry --target production .
docker tag cnc-api {{your_dockerhub_user}}/cnc-api:latest
docker push {{your_dockerhub_user}}/cnc-api:latest
```

You can also run all together in a single command:

```bash
docker buildx build --platform linux/arm/v7,linux/amd64 --tag {{your_dockerhub_user}}/cnc-api:latest --builder=raspberry --target production --push .
```

## Update the API in server

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

**NOTE:** We do not use the `--profile=ngrok` parameter because the ngrok service will be run locally, so we can place it "after" the Nginx reverse proxy. If you don't want to install and configure Nginx, just run the command with the `--profile=ngrok` parameter and the API will be publicly available.

# Database migrations

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

Then, follow the guide to [update Docker containers](#update-the-api-in-server) in the Raspberry.

# Nginx configuration

1. Copy from local machine to server:

- Nginx configuration file in `/nginx/api.conf` -> `/etc/nginx/api.conf`.

2. Restart Nginx:

```bash
$ sudo systemctl restart nginx
```
