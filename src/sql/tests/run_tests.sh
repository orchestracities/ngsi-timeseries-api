#!/usr/bin/env bash

cd ../../../
pytest src/sql/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
    --junitxml=test-results/junit-sql.xml
r=$?
cd -

exit $r
