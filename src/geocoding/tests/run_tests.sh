#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 8

docker run -ti --rm --network tests_geocodingtests quantumleap pytest geocoding/
r=$?

docker-compose down -v
exit $r
