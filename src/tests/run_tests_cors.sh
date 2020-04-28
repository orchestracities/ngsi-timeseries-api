#!/usr/bin/env bash

# Build Docker Image
docker build -t quantumleap_test -f ./../../Dockerfile_test ./../../
source ./../../deps.env

# ======= Part 1: CORS headers enabled ======= #

# Launch services, enable CORS headers for QL
QL_CORS_ALLOWED_ORIGIN=__ALL docker-compose -f docker-compose-test.yml up -d
sleep 12
tot=0

# Run CORS tests in quantumleap docker container # here we only run those methods that require a CORS header
docker exec \
  -e QL_URL=http://localhost:8668 \
  -e ORION_URL=http://orion:1026 \
  tests_quantumleap_1 sh -c \
  "pytest tests/test_cors.py -k test_cors_set --cov-report= --cov-config=.coveragerc --cov-append --cov=./"
tot=$?

docker-compose -f docker-compose-test.yml down

# ======= Part 2: CORS headers disabled (default behaviour) ======= #

QL_CORS_ALLOWED_ORIGIN= docker-compose -f docker-compose-test.yml up -d
docker exec \
  -e QL_URL=http://localhost:8668 \
  -e ORION_URL=http://orion:1026 \
  tests_quantumleap_1 sh -c \
  "pytest tests/test_cors.py -k test_cors_notset --cov-report= --cov-config=.coveragerc --cov-append --cov=./"
loc=$?
if [ "$tot" -eq 0 ]; then
  tot=$loc
fi
docker-compose -f docker-compose-test.yml down

echo ${tot}
exit ${tot}
