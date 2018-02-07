#!/bin/sh
. ./.env
uwsgi --http-auto-chunked --http-keepalive
