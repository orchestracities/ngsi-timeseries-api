#!/usr/bin/env bash

cd ../../../
pytest src/cache/ --cov-report= --cov-config=.coveragerc --cov-append --cov=src/ \
  --junitxml=test-results/junit-geocoding.xml
r=$?
cd -

exit $r
