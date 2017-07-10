#!/usr/bin/env bash

docker-compose up -d
sleep 8
docker run -ti --rm --network tests_reportertests quantumleap /bin/sh -c "pytest reporter/tests"
docker-compose down
