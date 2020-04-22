#!/usr/bin/env bash

docker build -t smartsdk/quantumleap ../../../

docker-compose up -d
sleep 8

cd ../../../
pytest src/geocoding/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/
r=$?
cd -

docker-compose down -v
exit $r
