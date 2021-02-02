#!/usr/bin/env bash

POSTGRES_PORT='5432'

docker build -t orchestracities/quantumleap ../../../

docker-compose up -d
sleep 20

cd ../../../
pytest src/reporter/ \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --ignore=src/reporter/tests/test_health.py
r=$?
cd -

unset POSTGRES_PORT

docker-compose down -v
exit $r
