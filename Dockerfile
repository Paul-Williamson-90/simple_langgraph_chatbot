# Dockerfile for Django frontend (VibedUI)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    DJANGO_SETTINGS_MODULE=langgraphweb.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Install Poetry (version 2.1.2 to match local)
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    /root/.local/bin/poetry self update 2.1.2 && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy only requirements first for caching
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && gunicorn langgraphweb.wsgi:application --bind 0.0.0.0:8000"]
