#!/bin/sh
. ./.env

until psql postgres://${CUSTOM_DATABASE_USER}:${CUSTOM_DATABASE_PASSWORD}@${CUSTOM_DATABASE_HOST}/${CUSTOM_DATABASE_NAME} -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

python manage.py migrate --noinput

python manage.py staffuser --superuser --email admin@fortana.co --password password

python manage.py runserver 0.0.0.0:8000
