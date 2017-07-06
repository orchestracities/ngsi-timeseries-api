#!/usr/bin/env bash

docker-compose up -d
sleep 5
docker run -ti --rm --network tests_clienttests quantumleap /bin/sh -c "pytest client/tests"
docker-compose down
