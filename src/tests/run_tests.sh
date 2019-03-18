#!/usr/bin/env bash

docker build -t quantumleap ../../.

# Load data with previous QL version
QL_IMAGE=smartsdk/quantumleap:0.5.1 docker-compose -f ../../docker/docker-compose-dev.yml up -d
sleep 60
docker run -ti --rm --network docker_default \
    -e ORION_URL="http://orion:1026" \
    -e QL_URL="http://quantumleap:8668" \
    quantumleap python tests/common.py

# Backwards Compatibility Test
docker-compose -f ../../docker/docker-compose-dev.yml stop quantumleap
QL_IMAGE=quantumleap docker-compose -f ../../docker/docker-compose-dev.yml up -d quantumleap
sleep 10
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
exit $tot
