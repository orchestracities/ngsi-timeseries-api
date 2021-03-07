#!/usr/bin/env bash
docker-compose build quantumleap-db-setup
docker-compose pull crate
docker-compose pull timescale
docker-compose pull redis

docker-compose up -d
sleep 20

cd ../../../
pytest src/reporter/ \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --ignore=src/reporter/tests/test_health.py \
       --junitxml=test-results/junit-reporter.xml
r=$?
cd -

docker-compose down -v
exit $r
