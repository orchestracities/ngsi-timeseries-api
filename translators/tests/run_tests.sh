#!/usr/bin/env bash

docker-compose up -d
sleep 10

docker run -ti --rm --network tests_translatorstests quantumleap pytest translators/tests
r=$?

docker-compose down
exit $r
