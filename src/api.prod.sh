#!/bin/sh
. ./.env

until psql postgres://${CUSTOM_DATABASE_USER}:${CUSTOM_DATABASE_PASSWORD}@${CUSTOM_DATABASE_HOST}/${CUSTOM_DATABASE_NAME} -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

uwsgi --http-auto-chunked --http-keepalive --ini uwsgi.ini
