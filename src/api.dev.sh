#!/bin/sh
. ./.env

until psql postgres://postgres:password@db/postgres -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

python manage.py migrate --noinput
python manage.py superuser --email $CUSTOM_SUPERUSER_EMAIL --password $CUSTOM_SUPERUSER_PASSWORD

python manage.py runserver 0.0.0.0:8000
