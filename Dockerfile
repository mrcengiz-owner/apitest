# Python base image
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies if needed (e.g. for psycopg2)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create persistent data directory for SQLite
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Use entrypoint script (handles migrate + createsuperuser + collectstatic + gunicorn)
ENTRYPOINT ["/app/entrypoint.sh"]
