#!/usr/bin/env bash

docker-compose up -d
sleep 10

docker run -ti --rm --network tests_reportertests quantumleap pytest reporter/tests
r=$?

docker-compose down
exit $r
