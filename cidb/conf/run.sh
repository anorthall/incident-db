#!/bin/bash
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
APP_ROOT="${PROJECT_ROOT}/"

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

if [ "$1" = "devserver" ]
then
    echo "Collecting static files..."
    cd "$APP_ROOT" || exit 1
    python manage.py collectstatic --noinput

    cd "$PROJECT_ROOT" || exit 1

    gunicorn \
      --bind "0.0.0.0:$PORT" \
      --workers 2 \
      --reload \
      --reload-engine inotify \
      --worker-class gthread \
      --name cidb-django \
      conf.wsgi:application
fi

if [ "$1" = "start" ]
then
    echo "Starting server..."
    gunicorn \
      --bind "0.0.0.0:$PORT" \
      --workers 4 \
      --preload \
      --max-requests 10000 \
      --max-requests-jitter 2000 \
      --worker-class gthread \
      --keep-alive 10 \
      --name cidb-django \
      conf.wsgi:application
fi
