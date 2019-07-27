#!/usr/bin/env bash

# Make sure **all** images are available before starting to test!
docker build -t quantumleap ../../../
docker-compose build
docker-compose pull --include-deps influx crate rethink timescale

docker-compose up -d
sleep 20

docker run -ti --rm --network tests_translatorstests quantumleap pytest translators/tests
r=$?

docker-compose down -v
exit $r
