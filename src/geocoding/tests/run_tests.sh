#!/usr/bin/env bash

docker-compose pull redis

docker-compose up -d
sleep 8

cd ../../../
pytest src/geocoding/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
  --junitxml=test-results/junit-geocoding.xml
r=$?
cd -

docker-compose down -v
exit $r
