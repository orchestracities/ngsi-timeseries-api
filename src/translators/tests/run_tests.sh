#!/usr/bin/env bash

docker build -t quantumleap ../../../

docker-compose up -d
sleep 20

cd ../../../
pytest src/translators/ --cov-report= --cov-config=.coveragerc --cov=src/
r=$?
cd -

docker-compose down -v
exit $r
