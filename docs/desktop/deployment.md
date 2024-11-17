# Deployment (Raspberry Pi)

## Overview

1. [Update files](#update-files).
1. [Update requirementss](#update-requirements).

# Introduction

In case you want to deploy to a Linux or Windows machine (x86), the steps are the same as in [development](./development.md) but using `requirements.txt` (or `environment.yml`) intead of the development requirements. This guide assumes you want to install and use the app in a Raspberry Pi.

The steps described in this guide were tested in the following device:
- **Board:** Raspberry Pi 3B+
- **OS:** Raspberry Pi OS (Bullseye, 32-bit)

# Update files

## Copy files to remote

In case you want to use just the strictly necessary files, the needed files and folders to run the app in production are:

```
    .
    ├── src                     # Source files
    │   ├── database            # Database models and CRUD
    │   ├── desktop             # UI components and utilities
    │   ├── schemas             # Data validation
    │   ├── utilities           # Various utilities
    │   ├── config.py           # Configuration management
    │   └── main.py             # Script to start app
    ├── deployment
    │   └── rpi
    │       └── requirements.desktop.txt
    └── docker-compose.yaml     # Docker containers orchestration
```

You can copy them by using [rsync](https://www.raspberrypi.com/documentation/computers/remote-access.html#using-rsync) or a FTP client like [FileZilla](https://docs.digitalocean.com/products/droplets/how-to/transfer-files/).

# Update requirements

In case you updated the `requirements` file:

```bash
# If you haven't, enter the project folder and activate the environment
$ cd remote-cnc
$ source venv/bin/activate

# Install the missing or new requirements
$ pip install -r deployment/rpi/requirements.desktop.txt
```
