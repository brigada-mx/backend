#!/bin/sh
set -e

until psql postgres://postgres:password@db/postgres -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

python manage.py migrate --noinput

exec "$@"
