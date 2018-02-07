#!/bin/sh
. ./.env
celery beat -A config
