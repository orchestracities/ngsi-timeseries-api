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
pytest src/reporter/tests/test_1T1E1A.py \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --junitxml=test-results/junit-reporter.xml
r=$?
cd -

docker-compose logs crate

docker-compose down -v
exit $r
