#!/bin/sh
. ./.env
celery worker -A config
