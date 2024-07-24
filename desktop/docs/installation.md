# Installation (Raspberry Pi)

## Overview

1. Set up Qt app.
1. Set up database.

# Introduction

In case you want to deploy to a Linux or Windows machine (x86), the steps are the same as in [development](./development.md) but using `requirements.txt` (or `environment.yml`) intead of the development requirements. This guide assumes you want to install and use the app in a Raspberry Pi with Docker installed.

The steps described in this guide were tested in the following device:
- **Board:** Raspberry Pi 3B+
- **OS:** Raspberry Pi OS (Bullseye, 32-bit)

# Set up Qt app

## Install dependencies

Before using the app for the first time you should run:

```bash
# Clone this project (unless you manually copied the files)
$ git clone https://github.com/Leandro-Bertoluzzi/remote-cnc

# 1. Access the repository and folder
$ cd remote-cnc/desktop

# 2. Install the needed global site-packages
$ sudo apt-get update
$ sudo apt-get install python3-pyqt5
$ sudo apt-get install python3-pyqt5.qtsvg
$ sudo apt-get install libpq5

# 3. Set up your Python environment
$ python -m venv --system-site-packages venv
$ source venv/bin/activate
$ pip install -r rpi/requirements.txt

# 4. Copy and configure the .env file
cp .env.example .env
```

## Run the Qt app

Once installed all dependencies and created the Python environment, every time you want to start the app you must run:

```bash
# 1. Activate your Python environment
$ source venv/bin/activate

# 2. Start the app
$ python main.py
```

## Configure the Qt app at startup

1. Move the `start.sh` bash script to your user's root folder.

```bash
$ mv /home/{{username}}/cnc-local-app/start.sh /home/{{username}}/start.sh
```
Note: Replace `{{username}}` by your actual user's name.

2. Assign execution permission to start script.

```bash
$ chmod +x start.sh
```

3. Create a `.desktop` file. A good explanation on why we use this method to run the app at startup, instead of others, can be found [here](https://learn.sparkfun.com/tutorials/how-to-run-a-raspberry-pi-program-on-startup/all).

```bash
$ mkdir /home/{{username}}/.config/autostart
$ nano /home/{{username}}/.config/autostart/cncmanager.desktop
```
Note: Replace `{{username}}` by your actual user's name.

4. Populate the `.desktop` file.

Copy the following text into the `cncmanager.desktop` file:

```bash
[Desktop Entry]
Version=1.0
Name=CNC Manager
Comment=Your comment
Exec=/home/{{username}}/start.sh
Icon=/usr/share/pixmaps/python3.xpm
Path=/home/{{username}}/
Terminal=false
StartupNotify=true
Type=Application
Categories=Utility;Application;
```
Note: Replace `{{username}}` by your actual user's name.

5. Reboot the device.

```bash
$ sudo reboot
```

## Initiate additional services

You can start containers for the required services via `docker compose`:
- PostgreSQL DB.
- Message broker (Redis).
- CNC worker.
- DB admin (adminer).

```bash
$ docker compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

# Set up database

You can execute the script `rpi/db_schema.py` in production with the `adminer` service, or copy it to the Raspberry and follow [these steps](../../rpi/db-management.md#execute-a-sql-script).
