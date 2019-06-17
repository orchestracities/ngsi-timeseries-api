#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 12

docker run -ti --rm --network tests_reportertests quantumleap pytest reporter/tests
r=$?

docker-compose down -v
exit $r
