#!/usr/bin/env bash

# Set test QL config file
export QL_CONFIG='src/reporter/tests/ql-config.yml'

cd ../../../
pytest src/reporter/ \
       --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
       --junitxml=test-results/junit-reporter.xml
r=$?
cd -

exit $r
