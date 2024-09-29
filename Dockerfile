# syntax=docker/dockerfile:1

# Base image
ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-alpine AS base

# Set environment variables for Poetry
ENV POETRY_VERSION=1.8
ENV POETRY_VIRTUALENVS_CREATE=false  

# Install Poetry and dependencies in a build stage
FROM base AS build
# Set working directory
WORKDIR /usr/src/app

# Install required packages
RUN apk add --no-cache build-base libffi-dev postgresql-dev musl-dev

# Copy the pyproject.toml and poetry.lock files to the container
COPY pyproject.toml poetry.lock* ./ 

# Install Poetry
RUN pip install poetry==${POETRY_VERSION}

# Install project dependencies without development dependencies
RUN poetry install --no-dev --no-root

# Final stage
FROM base AS final

# Prevents Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
ENV APP_ENVIRONMENT=production

# Install production dependencies
RUN apk add --no-cache postgresql-client

# Set working directory
WORKDIR /usr/src/app

# Copy the dependencies from build stage
COPY --from=build /usr/src/app /usr/src/app

# Copy the application code to the container
COPY . /usr/src/app

# Expose the port the app runs on
EXPOSE 8000

# Run the application using Poetry
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
