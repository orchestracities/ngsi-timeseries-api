#!/usr/bin/env bash

# Build Docker Image
docker build -t quantumleap ../../
source ./../../deps.env

# Launch services
QL_IMAGE=quantumleap docker-compose up -d
sleep 12

# Run CORS tests in quantumleap docker container
docker exec tests_quantumleap_1 sh -c \
  "QL_URL=http://quantumleap:8668 ORION_URL=http://orion:1026 pytest tests/test_cors.py --cov-report= --cov-config=.coveragerc --cov-append --cov=./"
tot=$?

docker-compose down
echo ${tot}
exit ${tot}
