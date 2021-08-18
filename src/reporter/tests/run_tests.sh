#!/usr/bin/env bash
docker-compose build quantumleap-db-setup
docker-compose pull crate
docker-compose pull timescale
docker-compose pull redis

docker-compose up -d
sleep 20

# Set test QL config file
export QL_CONFIG='src/reporter/tests/ql-config.yml'

cd ../../../
pytest src/reporter/ \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --junitxml=test-results/junit-reporter.xml
r=$?
cd -

docker-compose down -v
exit $r
