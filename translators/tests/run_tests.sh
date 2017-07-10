#!/usr/bin/env bash

docker-compose up -d
sleep 8
docker run -ti --rm --network tests_translatorstests quantumleap /bin/sh -c "pytest translators/tests"
docker-compose down
