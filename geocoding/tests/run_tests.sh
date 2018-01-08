#!/usr/bin/env bash

docker-compose up -d
sleep 5

docker run -ti --rm --network tests_geocodingtests quantumleap pytest geocoding/tests
r=$?

docker-compose down -v
exit $r
