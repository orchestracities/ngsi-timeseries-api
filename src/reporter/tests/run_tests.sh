#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 12

cd ../../../
pytest src/reporter/tests/test_version.py
r=$?
cd -

docker-compose down -v
exit $r
