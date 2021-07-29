#!/usr/bin/env bash

cd ../../../

pytest src/utils/ \
    --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
    --junitxml=test-results/junit-utils.xml

r=$?
cd -

exit $r
