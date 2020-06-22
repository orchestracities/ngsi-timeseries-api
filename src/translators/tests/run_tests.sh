#!/usr/bin/env bash

# Make sure **all** images are available before starting to test!
docker build -t smartsdk/quantumleap ../../../
docker-compose build quantumleap-db-setup
docker-compose pull influx
docker-compose pull crate
docker-compose pull rethink
docker-compose pull timescale
# NOTE. The below command:
#   docker-compose pull --include-deps influx crate rethink timescale
# fails on Travis for some obscure reasons which is why we're pulling
# one image at a time.

docker-compose up -d
sleep 20



cd ../../../

# Set Postgres port to same value as in docker-compose.yml
export POSTGRES_PORT='54320'
# Set test QL config file
export QL_CONFIG='src/translators/tests/ql-config.yml'

pytest src/translators/ --cov-report= --cov-config=.coveragerc --cov=src/
r=$?

unset POSTGRES_PORT
unset QL_CONFIG

cd -

docker-compose down -v
exit $r
