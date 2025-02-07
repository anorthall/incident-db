#!/bin/bash
CONF_ROOT="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="${CONF_ROOT}/.."
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
    echo "Starting server..."

    # shellcheck disable=SC2030
    granian --interface wsgi \
            --host 0.0.0.0 \
            --port "${PORT:=8000}" \
            --workers 1 \
            --respawn-failed-workers \
            --reload \
            --reload-paths backend/src \
            --no-ws \
            --threading-mode workers \
            conf.wsgi:application &
fi

# Run production server
if [ "$1" = "start" ]
then
    cd "$APP_ROOT" || exit 1

    echo "Collecting static files..."
    python manage.py collectstatic --no-input

    cd "$PROJECT_ROOT" || exit 1
    echo "Starting server..."
    # shellcheck disable=SC2031
    granian --interface wsgi \
            --host 0.0.0.0 \
            --port "${PORT:=8000}"  \
            --workers 4 \
            --respawn-failed-workers \
            --no-reload \
            --no-ws \
            --threading-mode workers \
            --workers-lifetime 600 \
            conf.wsgi:application &
fi
