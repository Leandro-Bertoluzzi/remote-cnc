# Initial server setup (Raspberry Pi)

## Overview

1. [Introduction](#introduction).
1. [Set up API](#set-up-api).
1. [Set up database](#set-up-database).
1. (Optional) [Set up reverse proxy](#optional-set-up-reverse-proxy).
1. [Set up remote access with Ngrok](#set-up-remote-access-with-ngrok).

# Introduction

This guide assumes you want to install and use the app in a Raspberry Pi.

The steps described in this guide were tested in the following device:
- **Board:** Raspberry Pi 3B+
- **OS:** Raspberry Pi OS (Bullseye, 32-bit)

# Set up API

(where from and to copy files, access with SSH/FileZilla, etc)

## Run the API

You can run the API in a Docker container. This will also start the following services:
- PostgreSQL DB.
- Message broker (Redis).
- CNC worker.
- DB admin (adminer).

```bash
$ docker compose -f docker-compose.yaml -f docker-compose.production.yaml up -d
```

# Set up database

You can execute the script `rpi/db_schema.py` in production with the `adminer` service, or copy it to the Raspberry and follow [these steps](./db-management.md#execute-a-sql-script).

# (Optional) Set up reverse proxy

Setting up a reverse proxy is certainly not mandatory, but it allows us to:
- Add HTTPS support to improve security.
- Configure redirections (HTTP 30x), useful if we want to modify a URL and still have access to it.
- Rename routes, for example “URL:8000/base” to “URL/api”.
- Use authentication and authorization previous to the endpoint.
- Enforce correct spelling of routes, for example enable “URL/login” but avoid “URL/login/”.
- Add a maintenance mode: Optionally show a fixed response when we are working on the API/Docker and the API is "down".

If you wonder why we don't run Nginx as a container, you can read an article justifying our philosofy [here](https://nickjanetakis.com/blog/why-i-prefer-running-nginx-on-my-docker-host-instead-of-in-a-container).

Moving forward, installing and configuring Nginx is pretty straightforward:

1. Install Nginx
```bash
sudo apt update
sudo apt install nginx
```
2. Copy the file `nginx/api.conf` in this repository to the folder `/etc/nginx` in your Raspberry Pi.
3. In your raspberry, open the file `/etc/nginx/nginx.conf` and add the following line inside the `http` section.
```bash
include /etc/nginx/api.conf; # All API configuration
```
4. Restart Nginx
```bash
sudo systemctl restart nginx
```

## Set up authentication in private routes

You can follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-set-up-password-authentication-with-nginx-on-ubuntu-22-04) to create a password file and the uncomment the authentication lines in `api.conf`.

# Set up remote access with Ngrok

## With Nginx (recommended)

If we are using Nginx as a reverse proxy, we must run Ngrok outside a container because otherwise we couldn't expose Nginx' port to the outside world.

1. Install the Ngrok client from [Ngrok downloads](https://ngrok.com/download) page, you can either download a zip and unzip it or use `apt install`.
2. Register Ngrok client, with the auth token in your [Ngrok profile](https://dashboard.ngrok.com/get-started/your-authtoken). If you don't have an account, create one.
```bash
ngrok authtoken {{NGROK_AUTHTOKEN}}
```
3. Start the ngrok client with a static domain. If you don't have one, you can create it [in your profile](https://dashboard.ngrok.com/get-started/your-authtoken).
```bash
ngrok http --domain={{NGROK_DOMAIN}} 80 --scheme http,https
```

### Configure Ngrok at startup

## Without Nginx

Just (re)run the `docker compose` file with the `ngrok` profile enabled.

```bash
$ docker compose -f docker-compose.yaml -f docker-compose.production.yaml--profile=ngrok up -d
```
