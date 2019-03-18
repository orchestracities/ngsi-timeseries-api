#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 16

docker run -ti --rm --network tests_translatorstests quantumleap pytest translators/tests
r=$?

docker-compose down -v
exit $r
