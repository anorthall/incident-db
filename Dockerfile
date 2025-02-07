# syntax=docker/dockerfile:1
FROM python:3.13-slim

ARG UV_VERSION=0.5.11

ENV PATH="/root/.local/bin:${PATH}"
ENV UV_PROJECT_ENVIRONMENT=/opt/uv/
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create directories
RUN mkdir -p /app /app/logs /app/src /opt/uv \
             /app/staticfiles /app/mediafiles

ADD https://astral.sh/uv/${UV_VERSION}/install.sh /uv-installer.sh
RUN chmod +x /uv-installer.sh && /uv-installer.sh && rm /uv-installer.sh

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    tini

COPY ./pyproject.toml ./uv.lock /app/
RUN groupadd app && useradd -g app -d /app app && chown app -R /app
RUN uv sync --frozen && chown app:app -R /opt/uv

COPY etc/run.sh /app
RUN chmod +x /app/run.sh

COPY ./reportdb/ /app/

USER app
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/run.sh", "start"]
