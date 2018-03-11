#!/bin/sh
. ./.env
rm -f celerybeat.pid
celery beat -A config
