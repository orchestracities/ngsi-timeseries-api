#!/usr/bin/env bash

cd ../../../

pytest src/wq/ \
    --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
    --junitxml=test-results/junit-wq.xml

r=$?
cd -

exit $r
