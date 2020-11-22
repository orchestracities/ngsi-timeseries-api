#!/usr/bin/env bash

docker build -t smartsdk/quantumleap ../../../

docker-compose -f docker-compose.timescale.yml up -d
sleep 10

cd ../../../

#pytest src/reporter/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
# TODO: comment in above and zap line below when Timescale backend
# is fully functional.

pytest src/reporter/ \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --ignore=src/reporter/tests/test_health.py \
       --ignore=src/reporter/tests/test_integration.py \
       --ignore=src/reporter/tests/test_multitenancy.py \
       --ignore=src/reporter/tests/test_notify.py \
       --ignore=src/reporter/tests/test_sql_injection.py \
       --ignore=src/reporter/tests/test_subscribe.py \
       --ignore=src/reporter/tests/test_time_format.py

r=$?
cd -

docker-compose -f docker-compose.timescale.yml down -v
exit $r

# NOTE. Ignored tests.
# See https://github.com/smartsdk/ngsi-timeseries-api/issues/378
