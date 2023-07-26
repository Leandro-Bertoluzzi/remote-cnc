# Pull official base image
FROM python:3.10.2-slim-buster

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
RUN pip install --upgrade pip
COPY ./pip/requirements.txt .
RUN pip install -r requirements.txt

# Copy necessary files
COPY ./config.py .
COPY ./database ./database
COPY ./utils ./utils
COPY ./worker ./worker

# Move to worker folder
WORKDIR /usr/src/app/worker
