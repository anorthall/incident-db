# syntax=docker/dockerfile:1
FROM python:3.12.0

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create directories
RUN mkdir -p /app /app/logs /app/src \
             /app/staticfiles /app/mediafiles

    # Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    tini

# Python packages
RUN pip install --upgrade pip
COPY ./requirements.txt /app
RUN pip install -r /app/requirements.txt

# Copy entrypoint
COPY etc/run.sh /app
RUN chmod +x /app/run.sh

# Copy app
COPY ./reportdb/ /app/src

# Final environment
RUN groupadd app
RUN useradd -g app -d /app app
RUN chown app -R /app
USER app
WORKDIR /app/src

# Entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/run.sh", "start"]
