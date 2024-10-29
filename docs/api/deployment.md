# Deploy changes (Raspberry Pi)

## Overview

1. [Deploy API](#deploy-api).
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

Then, follow the guide to [update Docker containers](../../README.md#update-docker-containers) in the Raspberry.

# Nginx configuration

1. Copy from local machine to server:

- Nginx configuration file in `/nginx/api.conf` -> `/etc/nginx/api.conf`.

2. Restart Nginx:

```bash
$ sudo systemctl restart nginx
```
