#!/usr/bin/env bash

docker-compose up -d
sleep 20

cd ../../../
pytest src/reporter/ \
       --cov-report --cov-config=.coveragerc --cov-append --cov=src/ \
       --ignore=src/reporter/tests/test_health.py
r=$?
cd -

docker-compose down -v
exit $r
