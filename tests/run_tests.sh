#!/usr/bin/env bash

export QL_IMAGE=quantumleap  # built in CI

docker-compose -f ../docker/docker-compose-dev.yml up -d
sleep 60

docker run -ti --rm --network docker_default \
    -e ORION_URL="http://orion:1026" \
    -e QL_URL="http://quantumleap:8668" \
    quantumleap pytest tests/test_integration.py
r=$?

docker-compose -f ../docker/docker-compose-dev.yml down -v
exit $r
