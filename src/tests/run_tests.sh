#!/usr/bin/env bash

# Prepare Docker Images
docker pull ${QL_PREV_IMAGE}
docker build -t quantumleap ../../
docker-compose -f ../../docker/docker-compose-dev.yml pull --ignore-pull-failures

tot=0

# Launch services with previous QL version
QL_IMAGE=${QL_PREV_IMAGE} docker-compose -f ../../docker/docker-compose-dev.yml up -d
sleep 10

ORION_HOST=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps | grep "1026" | awk '{ print $1 }')`
QUANTUMLEAP_HOST=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker ps | grep "8668" | awk '{ print $1 }')`

# Load data
docker run -ti --rm --network docker_default \
           -e ORION_URL="http://$ORION_HOST:1026" \
           -e QL_URL="http://$QUANTUMLEAP_HOST:8668" \
           quantumleap python tests/common.py

# Restart QL on development version
docker-compose -f ../../docker/docker-compose-dev.yml stop quantumleap
QL_IMAGE=quantumleap docker-compose -f ../../docker/docker-compose-dev.yml up -d quantumleap
sleep 10

# Backwards Compatibility Test
cd ../../
pytest src/tests/test_bc.py --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ 
tot=$?

# Integration Test
pytest src/tests/test_integration.py --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ 
loc=$?
if [ "$tot" -eq 0 ]; then
  tot=$loc
fi
cd -

docker-compose -f ../../docker/docker-compose-dev.yml down -v
exit ${tot}
