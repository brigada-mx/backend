#!/bin/sh
. ./.env

pgweb --url postgres://postgres:password@pg-919.cexrnsicl0n4.us-west-2.rds.amazonaws.com:5432/postgres --bind=0.0.0.0 --readonly --auth-user brigada --auth-pass $CUSTOM_PGWEB_PASSWORD
