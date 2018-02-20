#!/bin/sh
. ./.env
celery flower -A config --port=5555 --address=0.0.0.0 --url_prefix=flower --basic_auth=$CUSTOM_FLOWER_USERNAME:$CUSTOM_FLOWER_PASSWORD
