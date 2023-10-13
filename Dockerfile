# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
# Copy the source code into the container.
COPY . .
RUN mkdir -p logs
ENV PORT=8080

# Expose the port that the application listens on.
EXPOSE 8080

# Run the application.
CMD uvicorn 'main:app' --host=0.0.0.0 --port=8080
