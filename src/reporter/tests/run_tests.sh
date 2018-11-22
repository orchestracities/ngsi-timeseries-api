#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 20

docker run -ti --rm --network tests_reportertests quantumleap pytest reporter/tests
r=$?

docker-compose down
exit $r
