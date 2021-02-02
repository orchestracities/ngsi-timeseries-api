#!/usr/bin/env bash

# Prepare Docker Images
docker pull ${QL_PREV_IMAGE}
docker build -t orchestracities/quantumleap ../../
CRATE_VERSION=${PREV_CRATE} docker-compose pull --ignore-pull-failures

tot=0

# Launch services with previous CRATE and QL version
echo "\n"
echo "Launch services with previous CRATE and QL version"
CRATE_VERSION=${PREV_CRATE} QL_IMAGE=${QL_PREV_IMAGE} docker-compose up -d
sleep 20


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
           orchestracities/quantumleap python tests/common.py

# Restart QL on development version and CRATE on current version
docker-compose stop quantumleap
CRATE_VERSION=${CRATE_VERSION} QL_IMAGE=orchestracities/quantumleap docker-compose up -d
sleep 40

# Backwards Compatibility Test
echo "\n"
echo "Backwards Compatibility Test"
cd ../../
pytest src/tests/test_bc.py --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
tot=$?

# Integration Test
echo "\n"
echo "Integration Test"
pytest src/tests/test_integration.py --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
loc=$?
if [ "$tot" -eq 0 ]; then
  tot=$loc
fi
cd -

docker-compose down -v
exit ${tot}
