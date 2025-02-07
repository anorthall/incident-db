#!/bin/bash
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
APP_ROOT="${PROJECT_ROOT}/reportdb"

if [ -z "$VIRTUAL_ENV" ]
then
    echo "VIRTUAL_ENV is not set. Attempting to activate..."
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

if [ "$1" = "manage" ]
then
    cd "$APP_ROOT" || exit 1
    python manage.py "${@:2}"
fi

if [ "$1" = "test" ]
then
    cd "$APP_ROOT" || exit 1
    python manage.py test "${@:2}"
    exit 0
fi

# Run a development server which runs workers within the same
# docker container within a separate process for quicker builds
# and less RAM usage.
if [ "$1" = "devserver" ]
then
    echo "Collecting static files..."
    cd "$APP_ROOT" || exit 1
    python manage.py collectstatic --noinput

    if [ "$RUN_MIGRATIONS_ON_START" = "yes" ]
    then
        echo "Running migrations..."
        python manage.py migrate --no-input
    fi

    cd "$PROJECT_ROOT" || exit 1

    gunicorn \
      --bind "0.0.0.0:$PORT" \
      --workers 2 \
      --reload \
      --reload-engine inotify \
      --name incidentdb-django \
      conf.wsgi:application
fi

# Run production server
if [ "$1" = "start" ]
then
    NUM_CORES=$(nproc)
    NUM_WORKERS=$((NUM_CORES * 2 + 1))
    echo "Detected $NUM_CORES, running with $NUM_WORKERS workers"

    echo "Starting server..."
    gunicorn \
      --bind "0.0.0.0:$PORT" \
      --workers "$NUM_WORKERS" \
      --preload \
      --max-requests 1000 \
      --max-requests-jitter 200 \
      --keep-alive 10 \
      --name incidentdb-django \
      conf.wsgi:application
fi
