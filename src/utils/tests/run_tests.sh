#!/usr/bin/env bash

docker build -t quantumleap ../../../

cd ../../../
pytest src/utils/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/

exit $?
