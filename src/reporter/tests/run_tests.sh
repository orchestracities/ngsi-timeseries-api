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
       --ignore=src/reporter/tests/test_incomplete_entities.py \
       --ignore=src/reporter/tests/test_NTNE.py \
       --ignore=src/reporter/tests/test_NTNE1A.py \
       --ignore=src/reporter/tests/test_NTNENA.py \
       --ignore=src/reporter/tests/test_NTNE.py \
       --ignore=src/reporter/tests/test_op.py \
       --ignore=src/reporter/tests/test_sql_injection.py \
       --ignore=src/reporter/tests/test_time_format.py \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --junitxml=test-results/junit-reporter.xml

r=$?
cd -

docker-compose logs crate

docker-compose down -v
exit $r
