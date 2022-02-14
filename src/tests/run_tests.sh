#!/usr/bin/env bash

# Prepare Docker Images
docker pull orchestracities/quantumleap:${PREV_QL}
docker build -t orchestracities/quantumleap ../../
CRATE_VERSION=${PREV_CRATE} docker-compose -f docker-compose-bc.yml pull --ignore-pull-failures

tot=0

# Launch services with previous CRATE and QL version
echo "\n"
echo "Launch services with previous CRATE and QL version"

CRATE_VERSION=${PREV_CRATE} QL_VERSION=${PREV_QL} docker-compose -f docker-compose-bc.yml up -d

HOST="http://localhost:4200"
echo "Testing $HOST"
wait=0
while [ "$(curl -s -o /dev/null -L -w ''%{http_code}'' $HOST)" != "200" ] && [ $wait -le 30 ]
do
  echo "Waiting for $HOST"
  sleep 5
  wait=$((wait+5))
  echo "Elapsed time: $wait"
done

if [ $wait -gt 30 ]; then
  echo "timeout while waiting services to be ready"
  docker-compose -f docker-compose-bc.yml down -v
  exit -1
fi


ORION_BC_HOST=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps | grep "1026" | awk '{ print $1 }')`
QL_BC_HOST=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps | grep "8668" | awk '{ print $1 }')`

# Load data
echo "\n"
echo "Load data"
docker run -ti --rm --network tests_default \
           -e ORION_URL="http://$ORION_BC_HOST:1026" \
           -e QL_URL="http://$QL_BC_HOST:8668" \
           --entrypoint "" \
           -e USE_FLASK=TRUE \
           orchestracities/quantumleap:${PREV_QL} python tests/common.py

# Restart QL on development version and CRATE on current version
echo "\n"
echo "Use current version of ql and crate"

CRATE_VERSION=${CRATE_VERSION} QL_VERSION=latest docker-compose -f docker-compose-bc.yml stop quantumleap crate
CRATE_VERSION=${CRATE_VERSION} QL_VERSION=latest docker-compose -f docker-compose-bc.yml up -d

wait=0
while [ "$(curl -s -o /dev/null -L -w ''%{http_code}'' $HOST)" != "200" ] && [ $wait -le 30 ]
do
  echo "Waiting for $HOST"
  sleep 5
  wait=$((wait+5))
  echo "Elapsed time: $wait"
done

if [ $wait -gt 30 ]; then
  echo "timeout while waiting services to be ready"
  docker-compose -f docker-compose-bc.yml down -v
  exit -1
fi

# Backwards Compatibility Test
echo "\n"
echo "Backwards Compatibility Test"
cd ../../
pytest src/tests/test_bc.py --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
    --junitxml=test-results/junit-bc.xml
tot=$?

# Integration Test
echo "\n"
echo "Integration Test"
pytest -s src/tests/test_integration.py --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
    --junitxml=test-results/junit-it.xml
loc=$?
if [ "$tot" -eq 0 ]; then
  tot=$loc
fi
cd -

docker-compose -f docker-compose-bc.yml down -v

exit ${tot}
