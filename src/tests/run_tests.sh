#!/usr/bin/env bash

# Prepare Docker Images
docker pull ${QL_PREV_IMAGE}
docker build -t quantumleap ../../
docker-compose -f ../../docker/docker-compose-dev.yml pull --ignore-pull-failures

tot=0

# Launch services with previous QL version
QL_IMAGE=${QL_PREV_IMAGE} docker-compose -f ../../docker/docker-compose-dev.yml up -d
sleep 10

# Load data
docker run -ti --rm --network docker_default \
           -e ORION_URL="http://orion:1026" \
           -e QL_URL="http://quantumleap:8668" \
           quantumleap python tests/common.py

# Restart QL on development version
docker-compose -f ../../docker/docker-compose-dev.yml stop quantumleap
QL_IMAGE=quantumleap docker-compose -f ../../docker/docker-compose-dev.yml up -d quantumleap
sleep 10

# Backwards Compatibility Test
docker run -ti --rm --network docker_default \
    -e ORION_URL="http://orion:1026" \
    -e QL_URL="http://quantumleap:8668" \
    quantumleap pytest tests/test_bc.py
tot=$?

# Integration Test
docker run -ti --rm --network docker_default \
   -e ORION_URL="http://orion:1026" \
   -e QL_URL="http://quantumleap:8668" \
   quantumleap pytest tests/test_integration.py
loc=$?
if [ "$tot" -eq 0 ]; then
  tot=$loc
fi

docker-compose -f ../../docker/docker-compose-dev.yml down -v
exit ${tot}
