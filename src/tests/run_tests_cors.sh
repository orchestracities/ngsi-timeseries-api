#!/usr/bin/env bash

# Build Docker Image
docker build -t quantumleap_test -f ./../../Dockerfile_test ./../../
source ./../../deps.env

# Launch services
docker-compose -f docker-compose-test.yml up -d
sleep 12

# Run CORS tests in quantumleap docker container
docker exec tests_quantumleap_1 sh -c \
  "QL_URL=http://localhost:8668 ORION_URL=http://orion:1026 pytest tests/test_cors.py --cov-report= --cov-config=.coveragerc --cov-append --cov=./"
tot=$?

docker-compose -f docker-compose-test.yml down
echo ${tot}
exit ${tot}
