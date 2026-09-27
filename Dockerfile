FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV VIRTUAL_ENV=${UV_PROJECT_ENVIRONMENT}
ENV PYTHONPATH="/app/:/app/cidb/"
ENV PATH="/app/.venv/bin:${PATH}"
ENV DJANGO_SETTINGS_MODULE=cidb.conf.settings

RUN mkdir -p /app /app/staticfiles && \
    groupadd app && useradd -g app -d /app app && \
    chown -R app:app /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    tini && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --chown=app:app . .
USER app

# SECRET_KEY is scoped to collectstatic rather than baked in as an ENV, so an
# image that reaches production without a real key fails loudly instead of
# running with a publicly known one.
RUN uv sync --frozen && \
    SECRET_KEY=collectstatic-only uv run /app/cidb/manage.py collectstatic --noinput && \
    chmod +x /app/cidb/conf/run.sh

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/cidb/conf/run.sh", "start"]
