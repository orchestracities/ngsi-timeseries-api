#!/usr/bin/env bash

docker-compose up -d
sleep 10

docker run -ti --rm --network tests_clienttests quantumleap pytest client/tests
r=$?

docker-compose down
exit $r
