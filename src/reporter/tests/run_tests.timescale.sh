#!/usr/bin/env bash

docker build -t smartsdk/quantumleap ../../../

docker-compose -f docker-compose.timescale.yml up -d
sleep 10

# Set Postgres port to same value as in docker-compose.timescale.yml
export POSTGRES_PORT='54320'

cd ../../../

# pytest src/reporter/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
# TODO: comment in above and zap line below when Timescale backend
# is fully functional.

pytest src/reporter/tests/_tmptest_delete_with_timescale.py \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
r=$?
cd -

unset POSTGRES_PORT

docker-compose -f docker-compose.timescale.yml down -v
exit $r
