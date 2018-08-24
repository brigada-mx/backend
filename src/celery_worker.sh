#!/bin/sh
. ./.env
celery worker -A config -c 3 -Ofair
