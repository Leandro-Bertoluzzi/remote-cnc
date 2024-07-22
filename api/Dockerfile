FROM python:3.9 as base

FROM base as development

WORKDIR /app

# Install dependencies
COPY requirements-dev.txt ./
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements-dev.txt

# Copy project files
COPY . .

# Run uvicorn server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base as production

WORKDIR /app

# Add files from the build context to the container temporarily to execute a RUN instruction
# https://docs.docker.com/develop/develop-images/instructions/#add-or-copy
RUN --mount=type=bind,source=requirements.txt,target=/tmp/requirements.txt \
pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

# Copy project files
COPY ./core ./core
COPY ./middleware ./middleware
COPY ./routes ./routes
COPY ./services ./services
COPY app.py ./
COPY config.py ./

# If running behind a proxy like Nginx or Traefik add --proxy-headers
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--root-path", "/api"]
