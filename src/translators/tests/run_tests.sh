#!/usr/bin/env bash

# Make sure **all** images are available before starting to test!
docker build -t quantumleap ../../../
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

docker run -ti --rm --network tests_translatorstests quantumleap pytest translators/tests
r=$?

docker-compose down -v
exit $r
